import { test } from "node:test";
import assert from "node:assert/strict";
import { splitUploadBatches } from "../src/upload-batches.js";

test("large folders retain every input exactly once in bounded ordered batches", () => {
  const entries = Array.from({ length: 1101 }, (_, i) => ({ relativePath: `${i}.dcm`, file: { size: 1024 * 1024 } }));
  const batches = splitUploadBatches(entries);
  assert.deepEqual(batches.flat(), entries);
  assert.ok(batches.every((batch) => batch.length <= 500 && batch.reduce((sum, entry) => sum + entry.file.size, 0) <= 64 * 1024 * 1024));
});

test("empty or oversized selections fail before creating a cohort", () => {
  assert.throws(() => splitUploadBatches([]), /at least one/);
  assert.throws(() => splitUploadBatches([{ file: { size: 32 * 1024 * 1024 + 1 } }]), /32 MiB/);
  assert.equal(splitUploadBatches([{ file: { size: 32 * 1024 * 1024 } }]).length, 1);
});
