import { execSync } from "child_process";

const htmlPath = `${process.cwd()}/index.html`;
const out = "/tmp/2026.pdf";
const dest = `${process.env.HOME}/SynologyDrive/与手机共享/2026.pdf`;

execSync(`google-chrome --headless --disable-gpu --print-to-pdf="${out}" --no-pdf-header-footer "file://${htmlPath}"`, {
  stdio: "inherit",
});

execSync(`mv "${out}" "${dest}"`);
console.log(`moved -> ${dest}`);
