const DPR = Math.max(window.devicePixelRatio || 1, 2);
const PW = 780,
  PH = 1300;
const W = PW * 2;

import * as SunCalc from "suncalc";

const canvas = document.getElementById("c") as HTMLCanvasElement;
canvas.width = W * DPR;
canvas.height = PH * DPR;
canvas.style.width = `${W}px`;
canvas.style.height = `${PH}px`;

const ctx = canvas.getContext("2d")!;
ctx.scale(DPR, DPR);

// moon phase helper — adapted from reference implementation
function drawMoon(cx: number, cy: number, r: number, phase: number) {
  phase = phase % 1;
  if (phase < 0) phase += 1;

  // dark disk background
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fillStyle = "#ddd";
  ctx.fill();

  // lit portion (yellow)
  ctx.fillStyle = "#e8c830";
  ctx.beginPath();
  if (phase <= 0.5) {
    // waxing — lit on right
    ctx.arc(cx, cy, r, -Math.PI / 2, Math.PI / 2, false);
    const term = r - phase * 4 * r;
    if (phase <= 0.25) {
      ctx.ellipse(cx, cy, term, r, 0, Math.PI / 2, -Math.PI / 2, true);
    } else {
      ctx.ellipse(cx, cy, Math.abs(term), r, 0, Math.PI / 2, -Math.PI / 2, false);
    }
  } else {
    // waning — lit on left
    ctx.arc(cx, cy, r, Math.PI / 2, -Math.PI / 2, false);
    const term = r - (phase - 0.5) * 4 * r;
    if (phase <= 0.75) {
      ctx.ellipse(cx, cy, term, r, 0, -Math.PI / 2, Math.PI / 2, false);
    } else {
      ctx.ellipse(cx, cy, Math.abs(term), r, 0, -Math.PI / 2, Math.PI / 2, true);
    }
  }
  ctx.fill();

  // outline
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.strokeStyle = "#999";
  ctx.lineWidth = 0.8;
  ctx.stroke();
}

const pages = [0, PW];
const days = ["", "Mon 22", "Tue 23", "Wed 24", "Thu 25", "Fri 26", "Sat 27", "Sun 28"];
const CELL_W = PW / 2,
  CELL_H = PH / 2;
const G = 13;

// --- 13px grid (blue) ---
ctx.strokeStyle = "#aaccff";
ctx.lineWidth = 0.3;
pages.forEach((ox) => {
  for (let r = 0; r < 2; r++) {
    for (let c = 0; c < 2; c++) {
      const cx = ox + c * CELL_W,
        cy = r * CELL_H;
      for (let x = cx; x <= cx + CELL_W; x += G) {
        ctx.beginPath();
        ctx.moveTo(x, cy);
        ctx.lineTo(x, cy + CELL_H);
        ctx.stroke();
      }
      for (let y = cy; y <= cy + CELL_H; y += G) {
        ctx.beginPath();
        ctx.moveTo(cx, y);
        ctx.lineTo(cx + CELL_W, y);
        ctx.stroke();
      }
    }
  }
});

// --- cross lines (red) ---
ctx.strokeStyle = "#c33";
ctx.lineWidth = 1.5;
ctx.fillStyle = "#000";
ctx.font = "16px 'IBM 3270 Semi-Condensed'";
ctx.textAlign = "left";

pages.forEach((ox) => {
  ctx.beginPath();
  ctx.moveTo(ox + CELL_W, 0);
  ctx.lineTo(ox + CELL_W, PH);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(ox, CELL_H);
  ctx.lineTo(ox + PW, CELL_H);
  ctx.stroke();
});
// center spine line
ctx.beginPath();
ctx.moveTo(PW, 0);
ctx.lineTo(PW, PH);
ctx.stroke();

pages.forEach((ox, pi) => {
  for (let r = 0; r < 2; r++) {
    for (let c = 0; c < 2; c++) {
      const label = days[pi * 4 + r * 2 + c];
      if (label) {
        ctx.fillText(label, ox + c * CELL_W + 20, r * CELL_H + 36);
      }
    }
  }
});

// --- mini calendar (June 2026) top-left ---
const calX = 6,
  calY = 16;
const calCell = 55;
const monLabel = ["M", "T", "W", "T", "F", "S", "S"];
const juneDays = [
  1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
];
const juneStartDow = 0;

ctx.textAlign = "center";
ctx.textBaseline = "middle";

// month header
ctx.font = "bold 18px 'IBM 3270 Semi-Condensed'";
ctx.fillStyle = "#000";
ctx.fillText("June 2026", calX + 3.5 * calCell, calY);

// day-of-week headers
ctx.font = "13px 'IBM 3270 Semi-Condensed'";
const rowH = 32;
for (let i = 0; i < 7; i++) {
  ctx.fillStyle = i >= 5 ? "#c33" : "#888";
  ctx.fillText(monLabel[i], calX + i * calCell + calCell / 2, calY + 28);
}

// date cells
ctx.font = "16px 'IBM 3270 Semi-Condensed'";
let col = juneStartDow,
  row = 1;
juneDays.forEach((d) => {
  const cx = calX + col * calCell + calCell / 2;
  const cy = calY + 34 + row * rowH;
  ctx.fillStyle = col >= 5 ? "#c33" : "#000";
  ctx.fillText(d.toString(), cx, cy - 4);
  const moon = SunCalc.getMoonIllumination(new Date(Date.UTC(2026, 5, d, 12)));
  drawMoon(cx, cy + 14, 6, moon.phase);
  col++;
  if (col > 6) {
    col = 0;
    row++;
  }
});

ctx.textBaseline = "alphabetic";
ctx.textAlign = "left";

(window as any).savePDF = () => {
  const { jsPDF } = (window as any).jspdf;
  const pdf = new jsPDF({ orientation: "landscape", unit: "px", format: [W, PH] });
  pdf.addImage(canvas.toDataURL("image/png"), "PNG", 0, 0, W, PH);
  pdf.save("weekly.pdf");
};
