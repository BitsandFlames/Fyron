export function splitUploadBatches(entries) {
  const batches = [];
  let current = [], bytes = 0;
  for (const entry of entries) {
    if (entry.file.size > 32 * 1024 * 1024) {
      throw new Error("A file exceeds 32 MiB. Prepare smaller image previews before uploading.");
    }
    if (current.length && (bytes + entry.file.size > 64 * 1024 * 1024 || current.length >= 500)) {
      batches.push(current); current = []; bytes = 0;
    }
    current.push(entry); bytes += entry.file.size;
  }
  if (current.length) batches.push(current);
  if (!batches.length) throw new Error("Select at least one supported file.");
  return batches;
}
