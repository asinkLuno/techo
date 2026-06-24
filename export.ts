import { execSync } from "child_process";
import { unlinkSync } from "fs";

const args = process.argv.slice(2);
let start = "";
let end = "";
for (let i = 0; i < args.length; i++) {
  if (args[i] === "-s" && args[i + 1]) start = args[++i];
  else if (args[i] === "-e" && args[i + 1]) end = args[++i];
}

const params = new URLSearchParams({ mode: "export" });
if (start) params.set("start", start);
if (end) params.set("end", end);

const htmlPath = `file://${process.cwd()}/index.html?${params.toString()}`;
const label = start || end ? `${start || "000000"}-${end || "999999"}` : "2026";
const out = `/tmp/${label}.pdf`;
const dest = `${process.env.HOME}/SynologyDrive/与手机共享/${label}.pdf`;

execSync(
  `google-chrome --headless --disable-gpu --print-to-pdf="${out}" --no-pdf-header-footer "${htmlPath}"`,
  { stdio: "inherit" },
);

execSync(`mv "${out}" "${dest}"`);
console.log(`moved -> ${dest}`);
unlinkSync("export.cjs");
