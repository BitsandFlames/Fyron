import { afterEach, beforeEach, describe, expect, it } from "vitest";
import request from "supertest";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { createApp } from "../src/server.js";
import { probeImage } from "../src/image-probe.js";

const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=", "base64");
function fakeDatabase() {
  const cohorts = new Map(), images = new Map(), events = [];
  let sequence = 0;
  const match = (image, where = {}) => Object.entries(where).every(([key, value]) => image[key] === value);
  const db = {
    cohorts, images, events,
    cohort: {
      async create({ data }) { const row = { ...data, id: `cohort-${++sequence}` }; cohorts.set(row.id, row); return row; },
      async update({ where, data }) { const row = cohorts.get(where.id); Object.assign(row, data); return row; },
      async findUniqueOrThrow({ where }) { const row = cohorts.get(where.id); if (!row) throw new Error("Missing cohort"); return row; },
    },
    image: {
      async upsert({ where, create, update }) {
        let row = [...images.values()].find((image) => match(image, where.cohortId_relativePath));
        if (row) Object.assign(row, update);
        else { row = { ...create, id: `image-${++sequence}`, reviewState: "ACCEPTED" }; images.set(row.id, row); }
        return row;
      },
      async findMany({ where }) { return [...images.values()].filter((image) => match(image, where)); },
      async count({ where }) { return [...images.values()].filter((image) => match(image, where)).length; },
      async findUniqueOrThrow({ where, include }) { const row = images.get(where.id); return include?.cohort ? { ...row, cohort: cohorts.get(row.cohortId) } : row; },
      async update({ where, data }) { const row = images.get(where.id); Object.assign(row, data); return row; },
    },
    reviewEvent: {
      async count({ where }) { return events.filter((event) => event.imageId === where.imageId).length; },
      async create({ data }) { events.push({ ...data }); return data; },
    },
    export: { async create({ data }) { return { ...data, id: `export-${++sequence}` }; } },
    async $transaction(fn) { return fn(db); },
  };
  return db;
}

// Minimal Explicit VR Little Endian DICOM, generated in memory with synthetic UIDs.
function dicom(series, instance = 1) {
  function element(group, number, vr, value) {
    let bytes = Buffer.isBuffer(value) ? value : Buffer.from(String(value));
    if (bytes.length % 2) bytes = Buffer.concat([bytes, Buffer.from([vr === "UI" ? 0 : 32])]);
    const long = vr === "OW";
    const header = Buffer.alloc(long ? 12 : 8);
    header.writeUInt16LE(group, 0); header.writeUInt16LE(number, 2); header.write(vr, 4);
    if (long) header.writeUInt32LE(bytes.length, 8); else header.writeUInt16LE(bytes.length, 6);
    return Buffer.concat([header, bytes]);
  }
  const us = (value) => { const buffer = Buffer.alloc(2); buffer.writeUInt16LE(value); return buffer; };
  return Buffer.concat([Buffer.alloc(128), Buffer.from("DICM"),
    element(2, 0x10, "UI", "1.2.840.10008.1.2.1"),
    element(8, 0x18, "UI", `1.2.3.${series}.${instance}`),
    element(0x20, 0xd, "UI", "1.2.3"), element(0x20, 0xe, "UI", `1.2.3.${series}`),
    element(0x20, 0x13, "IS", instance), element(0x28, 2, "US", us(1)),
    element(0x28, 0x10, "US", us(2)), element(0x28, 0x11, "US", us(2)),
    element(0x28, 0x100, "US", us(16)), element(0x28, 0x103, "US", us(0)),
    element(0x7fe0, 0x10, "OW", Buffer.from([0, 0, 1, 0, 2, 0, 3, 0])),
  ]);
}

describe("Curate preserves original files and extraction completeness", () => {
  let root, db, app, cid;
  beforeEach(async () => {
    root = await fs.mkdtemp(path.join(os.tmpdir(), "fyron-curate-test-"));
    db = fakeDatabase();
    app = await createApp({ prisma: db, uploadRoot: path.join(root, "uploads"), exportRoot: path.join(root, "exports") });
    const response = await request(app).post("/api/cohorts").send({ name: "Synthetic test" }).expect(201);
    cid = response.body.id;
  });
  afterEach(async () => { await fs.rm(root, { recursive: true, force: true }); });
  function upload(files) {
    let req = request(app).post(`/api/cohorts/${cid}/images`).field("relativePaths", JSON.stringify(files.map(([name]) => name)));
    for (const [name, buffer] of files) req = req.attach("files", buffer, { filename: name });
    return req;
  }
  const source = () => db.cohorts.get(cid).sourceRoot;

  it("rejects changed duplicate bytes and preserves review evidence; identical retry is idempotent", async () => {
    await upload([["image.png", png]]).expect(201);
    const image = [...db.images.values()][0];
    await request(app).patch(`/api/images/${image.id}/review-state`).send({ reviewState: "REJECTED" }).expect(200);
    await upload([["image.png", Buffer.concat([png, Buffer.from("different")])]]).expect(409);
    await upload([["image.png", png]]).expect(201);
    expect(await fs.readFile(path.join(source(), "image.png"))).toEqual(png);
    expect(image.reviewState).toBe("REJECTED");
    expect(db.events).toHaveLength(1);
    expect(db.images.size).toBe(1);
  });

  it("preflights duplicate paths within a batch and traversal", async () => {
    await upload([["same.png", png], ["same.png", Buffer.concat([png, Buffer.from("other")])]]).expect(409);
    expect(db.images.size).toBe(0);
    for (const name of ["../escape.png", "..", "__dicom_metadata/studies.png", "C:/escape.png"]) {
      await upload([[name, png]]).expect(400);
    }
  });

  it("rejects the audited ICNS payload renamed as PNG and remains responsive", async () => {
    const payload = Buffer.alloc(16); payload.write("icns"); payload.writeUInt32BE(16, 4); payload.write("icp4", 8);
    await upload([["malformed.png", payload]]).expect(400);
    await request(app).get("/api/health").expect(200);
    await upload([["valid.png", png]]).expect(201);
  });

  it("preserves all incremental DICOM series and instances in an export", async () => {
    await upload([["a.dcm", dicom(21)]]).expect(201);
    await upload([["b.dcm", dicom(22)]]).expect(201);
    await upload([["c.dcm", dicom(21, 2)]]).expect(201);
    const response = await request(app).post(`/api/cohorts/${cid}/export-clean`).expect(201);
    const manifest = JSON.parse(await fs.readFile(path.join(response.body.exportRoot, "manifest.json"), "utf8"));
    expect(manifest.selectedDicomSeriesCount).toBe(2);
    const refs = manifest.images.flatMap((image) => image.dicomSeries.sourceRelativePaths);
    expect(refs.sort()).toEqual(["__dicom_source/a.dcm", "__dicom_source/b.dcm", "__dicom_source/c.dcm"]);
    expect(await fs.readFile(path.join(response.body.exportRoot, "dicom_series/1.2.3/1.2.3.21/a.dcm"))).toEqual(dicom(21));
    const reviewed = [...db.images.values()].find((image) => image.relativePath.includes("1.2.3.21"));
    await request(app).patch(`/api/images/${reviewed.id}/review-state`).send({ reviewState: "ACCEPTED" }).expect(200);
    await upload([["d.dcm", dicom(21, 3)]]).expect(409);
    await upload([["a.dcm", dicom(21)]]).expect(201);
    expect(db.events).toHaveLength(1);
  });

  it("fails exports on damaged or missing DICOM metadata", async () => {
    await upload([["a.dcm", dicom(21)]]).expect(201);
    const metadata = path.join(source(), "__dicom_metadata/studies.json");
    await fs.writeFile(metadata, "corrupt");
    await request(app).post(`/api/cohorts/${cid}/export-clean`).expect(409);
    await fs.rm(metadata);
    await request(app).post(`/api/cohorts/${cid}/export-clean`).expect(409);
    await upload([["a.dcm", dicom(21)]]).expect(409);
  });

  it("rejects cross-origin mutations and malformed image type claims", async () => {
    await request(app).post("/api/cohorts").set("Origin", "https://untrusted.example").send({ name: "blocked" }).expect(403);
    await upload([["disguised.jpg", png]]).expect(400);
    expect(db.images.size).toBe(0);
  });

  it("blocks export after an interrupted upload until the same batch is retried", async () => {
    const original = db.image.upsert;
    db.image.upsert = async () => { throw new Error("synthetic interruption"); };
    await upload([["image.png", png]]).expect(500);
    await request(app).post(`/api/cohorts/${cid}/export-clean`).expect(409);
    db.image.upsert = original;
    await upload([["different.png", png]]).expect(409);
    await upload([["image.png", png]]).expect(201);
    await request(app).post(`/api/cohorts/${cid}/export-clean`).expect(201);
  });
});

it("bounds parser execution time", async () => {
  await expect(probeImage(png, ".png", { timeoutMs: 1 })).rejects.toThrow(/malformed/);
  await expect(probeImage(png, ".png")).resolves.toEqual({ width: 1, height: 1 });
});
