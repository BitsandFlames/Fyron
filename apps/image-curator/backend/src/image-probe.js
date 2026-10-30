import { Worker } from "node:worker_threads";

export function probeImage(bytes, extension, { timeoutMs = 2000 } = {}) {
  return new Promise((resolve, reject) => {
    const worker = new Worker(new URL("./image-probe-worker.js", import.meta.url), {
      workerData: { bytes, extension }, resourceLimits: { maxOldGenerationSizeMb: 32 },
    });
    let settled = false;
    const finish = (result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      void worker.terminate();
      if (!result || result.error) {
        reject(Object.assign(new Error("Unsupported, malformed, or oversized image."), { status: 400 }));
      } else resolve(result);
    };
    const timer = setTimeout(() => finish(), timeoutMs);
    worker.once("message", finish);
    worker.once("error", () => finish());
    worker.once("exit", () => finish());
  });
}
