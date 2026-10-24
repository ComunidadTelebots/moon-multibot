import { readFileSync, writeFileSync } from "node:fs";

const snapshotPath = process.argv[2] || new URL(
  "../node_modules/@tgcloud/cli/src/core/snapshot.js",
  import.meta.url,
);
const original = `      const p = moduleToPath(moduleName);
      writeSnapshotFile(p, content);
      newPaths.add(p);`;
const patched = `      const p = moduleToPath(moduleName);
      // Telegram may return false tombstones for removed modules.
      if (typeof content !== "string") continue;
      writeSnapshotFile(p, content);
      newPaths.add(p);`;

const source = readFileSync(snapshotPath, "utf8");

if (source.includes(patched) || source.includes("if (typeof content !== 'string') continue;")) {
  console.log("tgcloud snapshot patch already applied");
} else if (source.includes(original)) {
  writeFileSync(snapshotPath, source.replace(original, patched));
  console.log("Applied tgcloud snapshot compatibility patch");
} else {
  console.warn("tgcloud snapshot patch was not needed or the CLI changed");
}
