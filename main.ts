import { getWeekDays, getMonthGrid, formatMonthYear, DAY_NAMES } from "./calendar";
import { drawMoon, getMoonPhase } from "./moon";

// --- constants ---
const DPR = Math.max(window.devicePixelRatio || 1, 2);
const PW = 780,
  PH = 1300;
const W = PW * 2;
const CELL_W = PW / 2,
  CELL_H = PH / 2;
const G = 13; // grid spacing

// --- reference date (change to advance/rewind the eternal calendar) ---
const REF = new Date();

// --- canvas setup ---
const canvas = document.getElementById("c") as HTMLCanvasElement;
canvas.width = W * DPR;
canvas.height = PH * DPR;
canvas.style.width = `${W}px`;
canvas.style.height = `${PH}px`;

const ctx = canvas.getContext("2d")!;
ctx.scale(DPR, DPR);

// ============================================================
// layout helpers
// ============================================================

function drawGrid() {
  ctx.strokeStyle = "#aaccff";
  ctx.lineWidth = 0.3;
  const pages = [0, PW];
  for (const ox of pages) {
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
  }
}

function drawCrossLines() {
  ctx.strokeStyle = "#c33";
  ctx.lineWidth = 1.5;
  const pages = [0, PW];
  for (const ox of pages) {
    ctx.beginPath();
    ctx.moveTo(ox + CELL_W, 0);
    ctx.lineTo(ox + CELL_W, PH);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(ox, CELL_H);
    ctx.lineTo(ox + PW, CELL_H);
    ctx.stroke();
  }
  // center spine
  ctx.beginPath();
  ctx.moveTo(PW, 0);
  ctx.lineTo(PW, PH);
  ctx.stroke();
}

function drawWeekLabels() {
  ctx.fillStyle = "#000";
  ctx.font = "16px 'IBM 3270 Semi-Condensed'";
  ctx.textAlign = "left";

  const week = getWeekDays(REF);
  const pages = [0, PW];
  let idx = 0;
  for (const ox of pages) {
    for (let r = 0; r < 2; r++) {
      for (let c = 0; c < 2; c++) {
        if (idx < week.length) {
          ctx.fillText(week[idx].label, ox + c * CELL_W + 20, r * CELL_H + 36);
        }
        idx++;
      }
    }
  }
}

// ============================================================
// mini calendar
// ============================================================

function drawMiniCalendar() {
  const calX = 6,
    calY = 16;
  const calCell = 55;
  const rowH = 32;

  const calMonth = REF.getMonth();
  const calYear = REF.getFullYear();
  const grid = getMonthGrid(calYear, calMonth);

  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  // month header
  ctx.font = "bold 18px 'IBM 3270 Semi-Condensed'";
  ctx.fillStyle = "#000";
  ctx.fillText(formatMonthYear(calYear, calMonth), calX + 3.5 * calCell, calY);

  // day-of-week headers
  ctx.font = "13px 'IBM 3270 Semi-Condensed'";
  for (let i = 0; i < 7; i++) {
    ctx.fillStyle = i >= 5 ? "#c33" : "#888";
    ctx.fillText(DAY_NAMES[i][0], calX + i * calCell + calCell / 2, calY + 28);
  }

  // date cells
  ctx.font = "16px 'IBM 3270 Semi-Condensed'";
  let row = 1;
  grid.forEach((cell, i) => {
    const col = i % 7;
    if (col === 0 && i > 0) row++;
    if (!cell) return;

    const cx = calX + col * calCell + calCell / 2;
    const cy = calY + 34 + row * rowH;
    ctx.fillStyle = col >= 5 ? "#c33" : "#000";
    ctx.fillText(cell.day.toString(), cx, cy - 4);

    // moon under date
    if (cell.date <= new Date()) {
      drawMoon(ctx, cx, cy + 14, 6, getMoonPhase(cell.date));
    }
  });

  ctx.textBaseline = "alphabetic";
  ctx.textAlign = "left";
}

// ============================================================
// render
// ============================================================

drawGrid();
drawCrossLines();
drawWeekLabels();
drawMiniCalendar();

// --- PDF export ---
(window as any).savePDF = () => {
  const { jsPDF } = (window as any).jspdf;
  const pdf = new jsPDF({ orientation: "landscape", unit: "px", format: [W, PH] });
  pdf.addImage(canvas.toDataURL("image/png"), "PNG", 0, 0, W, PH);
  pdf.save("weekly.pdf");
};
