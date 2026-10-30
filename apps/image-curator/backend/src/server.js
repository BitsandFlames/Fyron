import cors from "cors";
import express from "express";
import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import { PrismaClient } from "@prisma/client";
import dicomParser from "dicom-parser";
import multer from "multer";
import mime from "mime-types";
import { probeImage } from "./image-probe.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export async function createApp(options = {}) {
const prisma = options.prisma || new PrismaClient();
const app = express();
const upload = multer({
  storage: {
    _handleFile(req, file, callback) {
      const chunks = [];
      let size = 0;
      let failed = false;
      file.stream.on("data", (chunk) => {
        if (failed) return;
        req.uploadBytes = (req.uploadBytes || 0) + chunk.length;
        if (req.uploadBytes > 128 * 1024 * 1024) {
          if (!failed) callback(Object.assign(new Error("Upload exceeds 128 MiB; use smaller batches."), { status: 413 }));
          failed = true;
          chunks.length = 0;
          return;
        }
        size += chunk.length;
        chunks.push(chunk);
      });
      file.stream.on("error", (error) => { if (!failed) { failed = true; callback(error); } });
      file.stream.on("end", () => { if (!failed) callback(null, { buffer: Buffer.concat(chunks), size }); });
    },
    _removeFile(_req, file, callback) { delete file.buffer; callback(null); },
  },
  limits: {
    files: 12000,
    fileSize: 32 * 1024 * 1024,
    fieldSize: 2 * 1024 * 1024,
    fields: 4,
    parts: 12004
  }
});

const uploadRoot = options.uploadRoot || process.env.UPLOAD_ROOT || path.join(__dirname, "..", "data", "uploads");
const exportRoot = options.exportRoot || process.env.EXPORT_ROOT || path.join(__dirname, "..", "data", "exports");
const corsOrigin = process.env.CORS_ORIGIN || "http://localhost:5174";

const supportedExtensions = new Set([".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"]);
const dicomExtensions = new Set([".dcm", ".dicom", ".ima"]);
const dicomSourceRootName = "__dicom_source";
const dicomPreviewRootName = "__dicom_previews";
const dicomMetadataRootName = "__dicom_metadata";
const dicomMetadataFileName = "studies.json";
const sortKeys = new Set(["relativePath", "originalName", "sizeBytes", "createdAt", "updatedAt", "reviewState"]);
const selectionContextMaxLength = 2000;

app.use(cors({ origin: corsOrigin }));
app.use((req, res, next) => {
  if (req.get("origin") && req.get("origin") !== corsOrigin) {
    res.status(403).json({ error: "This local app does not accept requests from that origin." });
    return;
  }
  next();
});
app.use(express.json({ limit: "2mb" }));

// A single local API process owns these volumes. Serialize mutations through
// completion so uploads, reviews and exports see a consistent cohort revision.
let mutations = Promise.resolve();
function serial(handler) {
  return (req, res, next) => {
    const running = mutations.then(() => handler(req, res, next));
    mutations = running.catch(() => {});
    running.catch(next);
  };
}

function conflict(message = "An original file already exists with different contents.") {
  return Object.assign(new Error(message), { status: 409 });
}

async function checkOriginal(destination, bytes) {
  try {
    if (!(await fs.readFile(destination)).equals(bytes)) throw conflict();
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
}

async function writeOriginal(destination, bytes, sourceRoot) {
  await fs.mkdir(path.dirname(destination), { recursive: true });
  const temporary = path.join(sourceRoot, dicomMetadataRootName, `${randomUUID()}.tmp`);
  try {
    await fs.writeFile(temporary, bytes, { flag: "wx" });
    // Publish a complete original atomically, without replacing an existing file.
    try { await fs.link(temporary, destination); }
    catch (error) {
      if (error.code !== "EEXIST") throw error;
      await checkOriginal(destination, bytes);
    }
  } finally { await fs.rm(temporary, { force: true }); }
}

function assertCompleteUpload(cohort) {
  if (fsSync.existsSync(path.join(cohort.sourceRoot, dicomMetadataRootName, "pending-upload.json"))) {
    throw conflict("Upload is incomplete. Retry the same batch before reviewing or exporting.");
  }
}

function assertSafeRelativePath(relativePath) {
  const normalized = path.posix.normalize(String(relativePath || "").replaceAll("\\", "/"));
  if (!normalized || normalized === "." || normalized === ".." || normalized.includes("\0") || normalized.startsWith("../") || normalized.includes("/../") || path.isAbsolute(normalized) || /^[a-z]:/i.test(normalized)) {
    const error = new Error("Unsafe relative path");
    error.status = 400;
    throw error;
  }
  return normalized;
}

function getSupportedFileInfo(file, relativePath) {
  const normalized = assertSafeRelativePath(relativePath);
  const ext = path.extname(normalized).toLowerCase();
  if (!supportedExtensions.has(ext)) {
    return null;
  }
  const mimeType = mime.lookup(normalized) || "application/octet-stream";
  return { normalized, mimeType };
}

function isDicomCandidate(relativePath) {
  const normalized = assertSafeRelativePath(relativePath);
  const ext = path.extname(normalized).toLowerCase();
  const baseName = path.basename(normalized);
  return dicomExtensions.has(ext) || !baseName.includes(".");
}

function safeSegment(value, fallback = "unknown") {
  return String(value || fallback)
    .trim()
    .replace(/[^a-zA-Z0-9._-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .replace(/^\.+$/, "")
    .slice(0, 96) || fallback;
}

function normalizeSelectionContext(value) {
  const normalized = String(value || "").trim().slice(0, selectionContextMaxLength);
  return normalized || null;
}

function encodeCsv(rows) {
  return rows
    .map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(","))
    .join("\n");
}

function dicomString(dataSet, tag, fallback = "") {
  try {
    return String(dataSet.string(tag) || fallback).trim();
  } catch {
    return fallback;
  }
}

function dicomNumber(dataSet, tag, fallback = null) {
  try {
    const value = dataSet.string(tag);
    if (value == null || value === "") return fallback;
    const first = String(value).split("\\")[0];
    const parsed = Number(first);
    return Number.isFinite(parsed) ? parsed : fallback;
  } catch {
    return fallback;
  }
}

function dicomUInt16(dataSet, tag, fallback = null) {
  try {
    const value = dataSet.uint16(tag);
    return Number.isFinite(value) ? value : fallback;
  } catch {
    return fallback;
  }
}

function parseDicomFile(buffer, relativePath) {
  const byteArray = new Uint8Array(buffer);
  const dataSet = dicomParser.parseDicom(byteArray);
  const rows = dicomUInt16(dataSet, "x00280010", null);
  const columns = dicomUInt16(dataSet, "x00280011", null);
  return {
    dataSet,
    buffer,
    relativePath,
    studyUid: dicomString(dataSet, "x0020000d", "unknown-study"),
    seriesUid: dicomString(dataSet, "x0020000e", `series-${safeSegment(relativePath)}`),
    studyDescription: dicomString(dataSet, "x00081030", ""),
    seriesDescription: dicomString(dataSet, "x0008103e", ""),
    modality: dicomString(dataSet, "x00080060", ""),
    instanceNumber: dicomNumber(dataSet, "x00200013", 0),
    rows,
    columns,
    transferSyntax: dicomString(dataSet, "x00020010", "")
  };
}

function extractGrayscalePixels(dicom) {
  const { dataSet, buffer } = dicom;
  const rows = dicom.rows;
  const columns = dicom.columns;
  const pixelElement = dataSet.elements.x7fe00010;
  if (!rows || !columns || !pixelElement || pixelElement.fragments) {
    return null;
  }

  const samplesPerPixel = dicomUInt16(dataSet, "x00280002", 1);
  const bitsAllocated = dicomUInt16(dataSet, "x00280100", 16);
  const pixelRepresentation = dicomUInt16(dataSet, "x00280103", 0);
  if (samplesPerPixel !== 1 || (bitsAllocated !== 8 && bitsAllocated !== 16)) {
    return null;
  }

  const slope = dicomNumber(dataSet, "x00281053", 1) || 1;
  const intercept = dicomNumber(dataSet, "x00281052", 0) || 0;
  const center = dicomNumber(dataSet, "x00281050", null);
  const width = dicomNumber(dataSet, "x00281051", null);
  const pixelCount = rows * columns;
  if (pixelCount > 16_000_000 || pixelElement.dataOffset + pixelCount * (bitsAllocated / 8) > buffer.length) return null;
  const values = new Float32Array(pixelCount);
  let min = Infinity;
  let max = -Infinity;

  for (let index = 0; index < pixelCount; index += 1) {
    const offset = pixelElement.dataOffset + index * (bitsAllocated / 8);
    if (offset + (bitsAllocated / 8) > buffer.length) return null;
    const raw = bitsAllocated === 8
      ? buffer.readUInt8(offset)
      : pixelRepresentation === 1
        ? buffer.readInt16LE(offset)
        : buffer.readUInt16LE(offset);
    const value = raw * slope + intercept;
    values[index] = value;
    if (value < min) min = value;
    if (value > max) max = value;
  }

  const low = Number.isFinite(center) && Number.isFinite(width) && width > 1 ? center - width / 2 : min;
  const high = Number.isFinite(center) && Number.isFinite(width) && width > 1 ? center + width / 2 : max;
  const range = high > low ? high - low : 1;
  const grayscale = new Uint8Array(pixelCount);
  for (let index = 0; index < pixelCount; index += 1) {
    const scaled = Math.round(((values[index] - low) / range) * 255);
    grayscale[index] = Math.max(0, Math.min(255, scaled));
  }
  return { pixels: grayscale, width: columns, height: rows };
}

function downsampleGrayscale({ pixels, width, height }, maxSize = 224) {
  const scale = Math.min(1, maxSize / Math.max(width, height));
  const outWidth = Math.max(1, Math.round(width * scale));
  const outHeight = Math.max(1, Math.round(height * scale));
  if (outWidth === width && outHeight === height) {
    return { pixels, width, height };
  }
  const output = new Uint8Array(outWidth * outHeight);
  for (let y = 0; y < outHeight; y += 1) {
    const sourceY = Math.min(height - 1, Math.floor(y / scale));
    for (let x = 0; x < outWidth; x += 1) {
      const sourceX = Math.min(width - 1, Math.floor(x / scale));
      output[y * outWidth + x] = pixels[sourceY * width + sourceX];
    }
  }
  return { pixels: output, width: outWidth, height: outHeight };
}

function encodeBmp({ pixels, width, height }) {
  const rowSize = Math.ceil((width * 3) / 4) * 4;
  const pixelBytes = rowSize * height;
  const buffer = Buffer.alloc(54 + pixelBytes);
  buffer.write("BM", 0);
  buffer.writeUInt32LE(54 + pixelBytes, 2);
  buffer.writeUInt32LE(54, 10);
  buffer.writeUInt32LE(40, 14);
  buffer.writeInt32LE(width, 18);
  buffer.writeInt32LE(height, 22);
  buffer.writeUInt16LE(1, 26);
  buffer.writeUInt16LE(24, 28);
  buffer.writeUInt32LE(0, 30);
  buffer.writeUInt32LE(pixelBytes, 34);

  for (let y = 0; y < height; y += 1) {
    const targetRow = height - 1 - y;
    const rowOffset = 54 + targetRow * rowSize;
    for (let x = 0; x < width; x += 1) {
      const value = pixels[y * width + x];
      const offset = rowOffset + x * 3;
      buffer[offset] = value;
      buffer[offset + 1] = value;
      buffer[offset + 2] = value;
    }
  }
  return buffer;
}

function chooseMiddleDicom(series) {
  const sorted = [...series.files].sort((a, b) => {
    const byInstance = (a.instanceNumber || 0) - (b.instanceNumber || 0);
    return byInstance || a.relativePath.localeCompare(b.relativePath);
  });
  return sorted[Math.floor(sorted.length / 2)] || sorted[0] || null;
}

async function writeDicomMetadata(cohort, studies) {
  const metadataDir = path.join(cohort.sourceRoot, dicomMetadataRootName);
  await fs.mkdir(metadataDir, { recursive: true });
  const temporary = path.join(metadataDir, `${randomUUID()}.tmp`);
  try {
    await fs.writeFile(temporary, JSON.stringify({ version: 1, generatedAt: new Date().toISOString(), studies }, null, 2), { flag: "wx" });
    await fs.rename(temporary, path.join(metadataDir, dicomMetadataFileName));
  } finally { await fs.rm(temporary, { force: true }); }
}

async function readDicomMetadata(cohort) {
  const metadataPath = path.join(cohort.sourceRoot, dicomMetadataRootName, dicomMetadataFileName);
  try {
    const data = JSON.parse(await fs.readFile(metadataPath, "utf8"));
    if (!Array.isArray(data.studies) || data.studies.some((study) => !study.studyUid || !Array.isArray(study.series)
      || study.series.some((series) => !series.seriesUid || !series.thumbnailImageId
        || !Array.isArray(series.sourceRelativePaths) || !series.sourceRelativePaths.length))) {
      throw new Error("Invalid DICOM metadata");
    }
    return data.studies;
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw conflict("DICOM metadata cannot be read. Restore it before modifying or exporting this cohort.");
  }
}

function parseRelativePaths(body) {
  if (typeof body.relativePaths === "string") {
    try { return JSON.parse(body.relativePaths); }
    catch { throw Object.assign(new Error("relativePaths must be a JSON array."), { status: 400 }); }
  }
  if (Array.isArray(body.relativePaths)) {
    return body.relativePaths;
  }
  return [];
}

function publicCohort(cohort) {
  const accepted = cohort._count?.images ?? 0;
  return {
    id: cohort.id,
    name: cohort.name,
    selectionContext: cohort.selectionContext || null,
    createdAt: cohort.createdAt,
    sourceRoot: cohort.sourceRoot,
    status: cohort.status,
    imageCount: accepted,
    settings: cohort.settings || null,
    exports: cohort.exports || []
  };
}

async function ensureRootDirs() {
  await fs.mkdir(uploadRoot, { recursive: true });
  await fs.mkdir(exportRoot, { recursive: true });
}

app.get("/api/health", (_req, res) => {
  res.json({
    ok: true,
    service: "fyron-curate-api",
    timestamp: new Date().toISOString(),
    uploadRoot,
    exportRoot
  });
});

app.post("/api/cohorts", async (req, res, next) => {
  try {
    await ensureRootDirs();
    const name = String(req.body.name || "").trim() || "Untitled cohort";
    const selectionContext = normalizeSelectionContext(req.body.selectionContext);
    const cohort = await prisma.cohort.create({
      data: {
        name,
        selectionContext,
        sourceRoot: "",
        settings: { create: {} }
      },
      include: { settings: true, exports: true, _count: { select: { images: true } } }
    });
    const sourceRoot = path.join(uploadRoot, cohort.id);
    await fs.mkdir(sourceRoot, { recursive: true });
    const updated = await prisma.cohort.update({
      where: { id: cohort.id },
      data: { sourceRoot },
      include: { settings: true, exports: true, _count: { select: { images: true } } }
    });
    res.status(201).json(publicCohort(updated));
  } catch (error) {
    next(error);
  }
});

app.patch("/api/cohorts/:id", async (req, res, next) => {
  try {
    const name = String(req.body.name || "").trim() || "Untitled cohort";
    const selectionContext = normalizeSelectionContext(req.body.selectionContext);
    const cohort = await prisma.cohort.update({
      where: { id: req.params.id },
      data: { name, selectionContext },
      include: {
        settings: true,
        exports: { orderBy: { createdAt: "desc" }, take: 3 },
        _count: { select: { images: true } }
      }
    });
    res.json(publicCohort(cohort));
  } catch (error) {
    next(error);
  }
});

app.get("/api/cohorts", async (_req, res, next) => {
  try {
    const cohorts = await prisma.cohort.findMany({
      orderBy: { createdAt: "desc" },
      include: {
        settings: true,
        exports: { orderBy: { createdAt: "desc" }, take: 3 },
        _count: { select: { images: true } }
      }
    });
    res.json(cohorts.map(publicCohort));
  } catch (error) {
    next(error);
  }
});

app.post("/api/cohorts/:id/images", serial(async (req, res, next) => {
  try {
    await new Promise((resolve, reject) => upload.array("files")(req, res, (error) => error ? reject(error) : resolve()));
    const cohort = await prisma.cohort.findUniqueOrThrow({ where: { id: req.params.id } });
    const relativePaths = parseRelativePaths(req.body);
    const files = req.files || [];
    if (!Array.isArray(relativePaths) || !files.length || (relativePaths.length && relativePaths.length !== files.length)) {
      throw Object.assign(new Error("Provide files with one relative path per file."), { status: 400 });
    }
    let indexed = 0;
    let dicomFilesIndexed = 0;
    let dicomSeriesIndexed = 0;
    let skipped = 0;
    const dicomSeries = new Map();
    const previousStudies = await readDicomMetadata(cohort);
    const previousSeries = new Map(previousStudies.flatMap((study) => study.series.map((series) => [`${study.studyUid}::${series.seriesUid}`, series])));
    const prepared = [];
    const destinations = new Map();
    const digest = createHash("sha256");

    for (const [index, file] of files.entries()) {
      const candidatePath = relativePaths[index] || file.originalname;
      const normalized = assertSafeRelativePath(candidatePath);
      if ([dicomSourceRootName, dicomPreviewRootName, dicomMetadataRootName].includes(normalized.split("/")[0])) {
        throw Object.assign(new Error("Upload paths cannot use reserved internal directories."), { status: 400 });
      }
      const info = getSupportedFileInfo(file, candidatePath);
      if (!info && !isDicomCandidate(candidatePath)) {
        skipped += 1;
        continue;
      }

      const sourceRelativePath = info ? normalized : path.posix.join(dicomSourceRootName, normalized);
      const destination = path.join(cohort.sourceRoot, sourceRelativePath);
      const priorBytes = destinations.get(destination);
      if (priorBytes && !priorBytes.equals(file.buffer)) throw conflict("This batch contains conflicting duplicate filenames.");
      if (priorBytes) continue;
      destinations.set(destination, file.buffer);
      await checkOriginal(destination, file.buffer);
      digest.update(JSON.stringify(sourceRelativePath)).update(file.buffer);
      if (!info) {
        try {
          const dicom = parseDicomFile(file.buffer, normalized);
          if (![dicom.studyUid, dicom.seriesUid].every((uid) => uid.length <= 64 && /^(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*$/.test(uid))) {
            throw new Error("Invalid DICOM identifiers");
          }
          dicom.sourceRelativePath = sourceRelativePath;
          const key = `${dicom.studyUid}::${dicom.seriesUid}`;
          if (!dicomSeries.has(key)) {
            dicomSeries.set(key, {
              studyUid: dicom.studyUid,
              studyDescription: dicom.studyDescription,
              seriesUid: dicom.seriesUid,
              seriesDescription: dicom.seriesDescription,
              modality: dicom.modality,
              transferSyntax: dicom.transferSyntax,
              files: []
            });
          }
          dicomSeries.get(key).files.push(dicom);
          dicomFilesIndexed += 1;
          prepared.push({ file, destination });
        } catch {
          throw Object.assign(new Error("Malformed or unsupported DICOM file."), { status: 400 });
        }
        continue;
      }
      const dimensions = await probeImage(file.buffer, path.extname(normalized).toLowerCase());
      prepared.push({ file, destination, info, ...dimensions });
    }

    // Merge instance references before writing anything. A reviewed series is
    // immutable: adding instances requires a new cohort and a new review.
    for (const [key, series] of dicomSeries) {
      const previous = previousSeries.get(key);
      if (!previous) {
        const previewPath = path.posix.join(dicomPreviewRootName, safeSegment(series.studyUid), `${safeSegment(series.seriesUid)}.bmp`);
        const existing = await prisma.image.count({ where: { cohortId: cohort.id, relativePath: previewPath } });
        // A retry may have created this row before metadata publication. Only
        // permit that case while its matching upload is still pending.
        if (existing && !fsSync.existsSync(path.join(cohort.sourceRoot, dicomMetadataRootName, "pending-upload.json"))) {
          throw conflict("Existing DICOM preview has no source metadata. Restore metadata or use a new cohort.");
        }
      }
      if (previous) {
        const known = new Set(previous.sourceRelativePaths);
        const additions = series.files.filter((file) => !known.has(file.sourceRelativePath));
        if (additions.length && await prisma.reviewEvent.count({ where: { imageId: previous.thumbnailImageId } })) {
          throw conflict("This DICOM series has been reviewed. Import the expanded series into a new cohort.");
        }
        if (!additions.length) { dicomSeries.delete(key); continue; }
        const incoming = new Set(series.files.map((file) => file.sourceRelativePath));
        for (const relativePath of known) {
          if (incoming.has(relativePath)) continue;
          const sourcePath = path.join(cohort.sourceRoot, assertSafeRelativePath(relativePath));
          const parsed = parseDicomFile(await fs.readFile(sourcePath), relativePath);
          const { buffer, dataSet, ...metadata } = parsed;
          series.files.push({ ...metadata, sourceRelativePath: relativePath });
        }
      }
      let middle = chooseMiddleDicom(series);
      if (!middle.buffer) middle = parseDicomFile(await fs.readFile(path.join(cohort.sourceRoot, assertSafeRelativePath(middle.sourceRelativePath))), middle.relativePath);
      const pixels = extractGrayscalePixels(middle);
      if (!pixels) throw Object.assign(new Error("DICOM preview requires supported uncompressed grayscale pixels."), { status: 400 });
      series.middle = middle;
      series.thumbnail = downsampleGrayscale(pixels);
    }

    const pendingPath = path.join(cohort.sourceRoot, dicomMetadataRootName, "pending-upload.json");
    const batchHash = digest.digest("hex");
    await fs.mkdir(path.dirname(pendingPath), { recursive: true });
    try { await fs.writeFile(pendingPath, batchHash, { flag: "wx" }); }
    catch (error) {
      if (error.code !== "EEXIST") throw error;
      if (await fs.readFile(pendingPath, "utf8") !== batchHash) throw conflict("An interrupted upload must be retried with the same batch before adding files.");
    }
    for (const { file, destination, info, width, height } of prepared) {
      await writeOriginal(destination, file.buffer, cohort.sourceRoot);
      if (!info) continue;
      await prisma.image.upsert({
        where: { cohortId_relativePath: { cohortId: cohort.id, relativePath: info.normalized } },
        create: {
          cohortId: cohort.id,
          relativePath: info.normalized,
          originalName: path.basename(info.normalized),
          mimeType: info.mimeType,
          sizeBytes: file.size,
          width,
          height
        },
        update: {}
      });
      indexed += 1;
    }

    if (dicomSeries.size) {
      const studiesByUid = new Map(previousStudies.map((study) => [study.studyUid, study]));
      for (const series of dicomSeries.values()) {
        const { middle, thumbnail } = series;
        const bmp = encodeBmp(thumbnail);
        const studyKey = safeSegment(series.studyUid, "study");
        const seriesKey = safeSegment(series.seriesUid, "series");
        const previewRelativePath = path.posix.join(dicomPreviewRootName, studyKey, `${seriesKey}.bmp`);
        const previewDestination = path.join(cohort.sourceRoot, previewRelativePath);
        await fs.mkdir(path.dirname(previewDestination), { recursive: true });
        await fs.writeFile(previewDestination, bmp);
        const label = series.seriesDescription || `${series.modality || "DICOM"} series`;
        const image = await prisma.image.upsert({
          where: { cohortId_relativePath: { cohortId: cohort.id, relativePath: previewRelativePath } },
          create: {
            cohortId: cohort.id,
            relativePath: previewRelativePath,
            originalName: `${safeSegment(label, "dicom-series")}.bmp`,
            mimeType: "image/bmp",
            sizeBytes: bmp.length,
            width: thumbnail.width,
            height: thumbnail.height
          },
          update: {
            originalName: `${safeSegment(label, "dicom-series")}.bmp`,
            mimeType: "image/bmp",
            sizeBytes: bmp.length,
            width: thumbnail.width,
            height: thumbnail.height
          }
        });
        dicomSeriesIndexed += 1;
        indexed += 1;

        if (!studiesByUid.has(series.studyUid)) {
          studiesByUid.set(series.studyUid, {
            studyUid: series.studyUid,
            studyDescription: series.studyDescription,
            series: []
          });
        }
        const study = studiesByUid.get(series.studyUid);
        study.series = study.series.filter((item) => item.seriesUid !== series.seriesUid);
        study.series.push({
          seriesUid: series.seriesUid,
          seriesDescription: series.seriesDescription,
          modality: series.modality,
          transferSyntax: series.transferSyntax,
          imageCount: series.files.length,
          thumbnailImageId: image.id,
          thumbnailRelativePath: previewRelativePath,
          reviewState: image.reviewState,
          sourceRelativePaths: series.files.map((item) => item.sourceRelativePath),
          width: middle.columns,
          height: middle.rows
        });
      }
      const studies = [...studiesByUid.values()].sort((a, b) => {
        const left = a.studyDescription || a.studyUid;
        const right = b.studyDescription || b.studyUid;
        return left.localeCompare(right);
      });
      await writeDicomMetadata(cohort, studies);
    }

    const imageCount = await prisma.image.count({ where: { cohortId: cohort.id } });
    await fs.rm(pendingPath);
    res.status(201).json({ cohortId: cohort.id, indexed, skipped, imageCount, dicomFilesIndexed, dicomSeriesIndexed });
  } catch (error) {
    next(error);
  }
}));

app.get("/api/cohorts/:id/dicom-studies", async (req, res, next) => {
  try {
    const cohort = await prisma.cohort.findUniqueOrThrow({ where: { id: req.params.id } });
    const studies = await readDicomMetadata(cohort);
    const imageIds = studies.flatMap((study) => study.series || []).map((series) => series.thumbnailImageId).filter(Boolean);
    const images = imageIds.length
      ? await prisma.image.findMany({ where: { id: { in: imageIds } } })
      : [];
    const imagesById = new Map(images.map((image) => [image.id, image]));
    const enriched = studies.map((study) => ({
      ...study,
      series: (study.series || []).map((series) => ({
        ...series,
        reviewState: imagesById.get(series.thumbnailImageId)?.reviewState || series.reviewState || "ACCEPTED"
      }))
    }));
    res.json({ cohortId: cohort.id, studies: enriched });
  } catch (error) {
    next(error);
  }
});

app.get("/api/cohorts/:id/images", async (req, res, next) => {
  try {
    const filter = req.query.filter;
    const search = String(req.query.search || "").trim();
    const sortKey = sortKeys.has(String(req.query.sortKey)) ? String(req.query.sortKey) : "relativePath";
    const sortDirection = req.query.sortDirection === "desc" ? "desc" : "asc";
    const where = {
      cohortId: req.params.id,
      ...(filter === "accepted" ? { reviewState: "ACCEPTED" } : {}),
      ...(filter === "rejected" ? { reviewState: "REJECTED" } : {}),
      ...(search ? { relativePath: { contains: search, mode: "insensitive" } } : {})
    };
    const [cohort, images, counts] = await Promise.all([
      prisma.cohort.findUniqueOrThrow({ where: { id: req.params.id }, include: { settings: true, exports: { orderBy: { createdAt: "desc" } } } }),
      prisma.image.findMany({ where, orderBy: { [sortKey]: sortDirection } }),
      prisma.image.groupBy({ by: ["reviewState"], where: { cohortId: req.params.id }, _count: true })
    ]);
    const reviewedEvents = await prisma.reviewEvent.findMany({
      where: { image: { cohortId: req.params.id } },
      distinct: ["imageId"],
      select: { imageId: true }
    });
    const reviewCounts = { accepted: 0, rejected: 0 };
    for (const count of counts) {
      reviewCounts[count.reviewState.toLowerCase()] = count._count;
    }
    res.json({
      cohort,
      images,
      counts: reviewCounts,
      reviewedImageIds: reviewedEvents.map((event) => event.imageId)
    });
  } catch (error) {
    next(error);
  }
});

app.patch("/api/images/:id/review-state", serial(async (req, res, next) => {
  try {
    const image = await prisma.image.findUniqueOrThrow({ where: { id: req.params.id } });
    assertCompleteUpload(await prisma.cohort.findUniqueOrThrow({ where: { id: image.cohortId } }));
    const requested = req.body.reviewState;
    const nextState = requested === "ACCEPTED" || requested === "REJECTED"
      ? requested
      : image.reviewState === "ACCEPTED" ? "REJECTED" : "ACCEPTED";

    const updated = await prisma.$transaction(async (tx) => {
      const changed = await tx.image.update({ where: { id: image.id }, data: { reviewState: nextState } });
      await tx.reviewEvent.create({
        data: {
          imageId: image.id,
          action: image.reviewState === nextState ? "review_state_confirmed" : "review_state_changed",
          previousState: image.reviewState,
          nextState
        }
      });
      return changed;
    });

    res.json(updated);
  } catch (error) {
    next(error);
  }
}));

app.patch("/api/cohorts/:id/settings", async (req, res, next) => {
  try {
    const imageSize = Number(req.body.imageSize);
    const gapSize = Number(req.body.gapSize);
    const imageFit = req.body.imageFit === "contain" ? "contain" : "cover";
    const sortKey = sortKeys.has(String(req.body.sortKey)) ? String(req.body.sortKey) : "relativePath";
    const sortDirection = req.body.sortDirection === "desc" ? "desc" : "asc";
    const data = {
      imageSize: Number.isFinite(imageSize) ? Math.min(Math.max(Math.round(imageSize), 96), 420) : 180,
      gapSize: Number.isFinite(gapSize) ? Math.min(Math.max(Math.round(gapSize), 4), 32) : 12,
      imageFit,
      sortKey,
      sortDirection
    };
    const settings = await prisma.gallerySettings.upsert({
      where: { cohortId: req.params.id },
      create: { cohortId: req.params.id, ...data },
      update: data
    });
    res.json(settings);
  } catch (error) {
    next(error);
  }
});

app.post("/api/cohorts/:id/export-clean", serial(async (req, res, next) => {
  let stagingDirectory;
  try {
    const cohort = await prisma.cohort.findUniqueOrThrow({ where: { id: req.params.id } });
    assertCompleteUpload(cohort);
    await prisma.cohort.update({ where: { id: cohort.id }, data: { status: "EXPORTING" } });
    const publishedDirectory = path.join(exportRoot, cohort.id, `${new Date().toISOString().replaceAll(":", "-")}-${randomUUID()}`);
    const exportDirectory = `${publishedDirectory}.partial`;
    stagingDirectory = exportDirectory;
    await fs.mkdir(exportDirectory, { recursive: true });

    const acceptedImages = await prisma.image.findMany({ where: { cohortId: cohort.id, reviewState: "ACCEPTED" } });
    const rejectedCount = await prisma.image.count({ where: { cohortId: cohort.id, reviewState: "REJECTED" } });
    const dicomStudies = await readDicomMetadata(cohort);
    const dicomSeriesByThumbnail = new Map();
    for (const study of dicomStudies) {
      for (const series of study.series || []) {
        if (series.thumbnailImageId) {
          dicomSeriesByThumbnail.set(series.thumbnailImageId, { study, series });
        }
      }
    }
    const manifestRows = [
      ["id", "relative_path", "original_name", "mime_type", "size_bytes", "width", "height", "review_state"]
    ];

    for (const image of acceptedImages) {
      const relativePath = assertSafeRelativePath(image.relativePath);
      const source = path.join(cohort.sourceRoot, relativePath);
      const destination = path.join(exportDirectory, relativePath);
      await fs.mkdir(path.dirname(destination), { recursive: true });
      await fs.copyFile(source, destination);
      manifestRows.push([
        image.id,
        image.relativePath,
        image.originalName,
        image.mimeType,
        String(image.sizeBytes),
        image.width == null ? "" : String(image.width),
        image.height == null ? "" : String(image.height),
        image.reviewState
      ]);

      const dicomMatch = dicomSeriesByThumbnail.get(image.id);
      if (relativePath.startsWith(`${dicomPreviewRootName}/`) && !dicomMatch) {
        throw conflict("DICOM source metadata is missing; export cannot be completed.");
      }
      if (dicomMatch) {
        const studyKey = safeSegment(dicomMatch.study.studyUid, "study");
        const seriesKey = safeSegment(dicomMatch.series.seriesUid, "series");
        for (const sourceRelativePath of dicomMatch.series.sourceRelativePaths || []) {
          const safeSourceRelativePath = assertSafeRelativePath(sourceRelativePath);
          const sourceFile = path.join(cohort.sourceRoot, safeSourceRelativePath);
          const originalRelativePath = safeSourceRelativePath.startsWith(`${dicomSourceRootName}/`)
            ? safeSourceRelativePath.slice(dicomSourceRootName.length + 1)
            : safeSourceRelativePath;
          const seriesDestination = path.join(exportDirectory, "dicom_series", studyKey, seriesKey, originalRelativePath);
          await fs.mkdir(path.dirname(seriesDestination), { recursive: true });
          await fs.copyFile(sourceFile, seriesDestination);
        }
      }
    }
    const manifest = {
      cohortId: cohort.id,
      cohortName: cohort.name,
      exportedAt: new Date().toISOString(),
      acceptedCount: acceptedImages.length,
      rejectedCount,
      selectedDicomSeriesCount: acceptedImages.filter((image) => dicomSeriesByThumbnail.has(image.id)).length,
      images: acceptedImages.map((image) => ({
        id: image.id,
        relativePath: image.relativePath,
        originalName: image.originalName,
        mimeType: image.mimeType,
        sizeBytes: image.sizeBytes,
        width: image.width,
        height: image.height,
        reviewState: image.reviewState,
        dicomSeries: dicomSeriesByThumbnail.has(image.id)
          ? {
              studyUid: dicomSeriesByThumbnail.get(image.id).study.studyUid,
              seriesUid: dicomSeriesByThumbnail.get(image.id).series.seriesUid,
              sourceRelativePaths: dicomSeriesByThumbnail.get(image.id).series.sourceRelativePaths || []
            }
          : null
      }))
    };
    const csv = encodeCsv(manifestRows);
    await fs.writeFile(path.join(exportDirectory, "manifest.csv"), `${csv}\n`, "utf8");
    await fs.writeFile(path.join(exportDirectory, "manifest.json"), JSON.stringify(manifest, null, 2), "utf8");
    await fs.rename(exportDirectory, publishedDirectory);
    stagingDirectory = null;

    const exportRecord = await prisma.export.create({
      data: {
        cohortId: cohort.id,
        exportRoot: publishedDirectory,
        acceptedCount: acceptedImages.length,
        rejectedCount
      }
    });
    await prisma.cohort.update({ where: { id: cohort.id }, data: { status: "EXPORTED" } });
    res.status(201).json(exportRecord);
  } catch (error) {
    if (stagingDirectory) await fs.rm(stagingDirectory, { recursive: true, force: true }).catch(() => {});
    await prisma.cohort.update({ where: { id: req.params.id }, data: { status: "ERROR" } }).catch(() => {});
    next(error);
  }
}));

app.get("/api/cohorts/:id/review-labels.csv", async (req, res, next) => {
  try {
    const cohort = await prisma.cohort.findUniqueOrThrow({ where: { id: req.params.id } });
    assertCompleteUpload(cohort);
    const [images, reviewedEvents] = await Promise.all([
      prisma.image.findMany({
        where: { cohortId: cohort.id },
        orderBy: { relativePath: "asc" }
      }),
      prisma.reviewEvent.findMany({
        where: { image: { cohortId: cohort.id } },
        distinct: ["imageId"],
        select: { imageId: true }
      })
    ]);
    if (!images.length) {
      res.status(409).json({ error: "Cannot export labels for an empty cohort." });
      return;
    }
    if (reviewedEvents.length !== images.length) {
      res.status(409).json({
        error: `Review all images before exporting labels (${reviewedEvents.length}/${images.length} reviewed).`
      });
      return;
    }
    const rows = [
      ["filename", "status"],
      ...images.map((image) => [image.relativePath, image.reviewState.toLowerCase()])
    ];
    const fileName = `${safeSegment(cohort.name, "cohort")}-review-labels.csv`;
    res.type("text/csv");
    res.attachment(fileName);
    res.send(`${encodeCsv(rows)}\n`);
  } catch (error) {
    next(error);
  }
});

app.get("/api/files/:imageId", async (req, res, next) => {
  try {
    const image = await prisma.image.findUniqueOrThrow({
      where: { id: req.params.imageId },
      include: { cohort: true }
    });
    const relativePath = assertSafeRelativePath(image.relativePath);
    const filePath = path.join(image.cohort.sourceRoot, relativePath);
    if (!fsSync.existsSync(filePath)) {
      res.status(404).json({ error: "File not found" });
      return;
    }
    res.type(image.mimeType);
    res.sendFile(filePath);
  } catch (error) {
    next(error);
  }
});

app.use((error, _req, res, _next) => {
  const status = error.status || (error instanceof multer.MulterError ? 413 : error.name === "NotFoundError" ? 404 : 500);
  res.status(status).json({
    error: status === 500 ? "Internal server error" : error.message
  });
  if (status === 500) {
    console.error("Curate request failed (internal error).");
  }
});

await ensureRootDirs();
return app;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const app = await createApp();
  const port = Number(process.env.PORT || 4000);
  const server = app.listen(port, () => console.log(`Image curator API listening on ${port}`));
  server.requestTimeout = 60_000;
}
