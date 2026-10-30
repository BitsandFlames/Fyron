import { parentPort, workerData } from "node:worker_threads";
import { imageSize } from "image-size";

try {
  const bytes = Buffer.from(workerData.bytes);
  // Reject formats outside Curate's raster allowlist before invoking a parser.
  const magic = bytes.subarray(0, 12).toString("hex");
  const allowed = magic.startsWith("89504e470d0a1a0a") || magic.startsWith("ffd8ff")
    || magic.startsWith("474946383761") || magic.startsWith("474946383961")
    || magic.startsWith("424d") || magic.startsWith("49492a00") || magic.startsWith("4d4d002a")
    || (bytes.toString("ascii", 0, 4) === "RIFF" && bytes.toString("ascii", 8, 12) === "WEBP");
  if (!allowed) throw new Error("Unsupported image");
  const dimensions = imageSize(bytes);
  const types = { png: [".png"], jpg: [".jpg", ".jpeg"], gif: [".gif"], bmp: [".bmp"],
    tiff: [".tif", ".tiff"], webp: [".webp"] };
  if (!types[dimensions.type]?.includes(workerData.extension)
      || !Number.isSafeInteger(dimensions.width) || !Number.isSafeInteger(dimensions.height)
      || dimensions.width <= 0 || dimensions.height <= 0
      || dimensions.width * dimensions.height > 100_000_000) throw new Error("Invalid image dimensions or type");
  parentPort.postMessage({ width: dimensions.width, height: dimensions.height });
} catch {
  parentPort.postMessage({ error: true });
}
