import { getMonthGrid, MONTH_NAMES, DAY_NAMES } from "./calendar";
import { drawMoon, getMoonPhase, getEarthPhase, getTranquilityBaseStatus, LunarBaseStatus } from "./moon";
import { CLR } from "./colors";

// --- constants ---
const DPR = Math.max(window.devicePixelRatio || 1, 2);
const PW = 780;
const MONTH_H = 1300;
const W = PW * 2; // 1560
const SPLIT = PW;

const REF = new Date();
const YEAR = REF.getFullYear();
const MONTH = REF.getMonth();
const DAYS_IN_MONTH = new Date(YEAR, MONTH + 1, 0).getDate();
const NUM_ROWS = Math.ceil((new Date(YEAR, MONTH, 1).getDay() + DAYS_IN_MONTH) / 7);
const WD_ABBR = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

// precompute day status for month days
const BASE: LunarBaseStatus[] = [];
for (let d = 1; d <= DAYS_IN_MONTH; d++) {
  BASE.push(getTranquilityBaseStatus(new Date(YEAR, MONTH, d, 12)));
}

function dayIsDaytime(date: Date): boolean {
  return getTranquilityBaseStatus(date).isDaytime;
}

// compute all weeks that touch this month (Mon–Sun)
interface WeekSpan {
  label: string;
  days: { date: Date; inMonth: boolean }[];
}
const WEEKS: WeekSpan[] = [];
{
  // a week belongs to the month whose 1st falls within it
  const thisFirst = new Date(YEAR, MONTH, 1);
  const nextFirst = new Date(YEAR, MONTH + 1, 1);
  const start = new Date(thisFirst);
  start.setDate(start.getDate() - ((start.getDay() + 6) % 7)); // Monday of week containing 1st
  const end = new Date(nextFirst);
  end.setDate(end.getDate() - ((end.getDay() + 6) % 7)); // Monday of week containing next month's 1st

  const cursor = new Date(start);
  while (cursor < end) {
    const days: WeekSpan["days"] = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(cursor);
      days.push({ date: d, inMonth: d.getMonth() === MONTH });
      cursor.setDate(cursor.getDate() + 1);
    }
    const mon = days[0].date,
      sun = days[6].date;
    WEEKS.push({
      label: `${DAY_NAMES[mon.getDay()]} ${mon.getDate()} – ${DAY_NAMES[sun.getDay()]} ${sun.getDate()}`,
      days,
    });
  }
}

const TOTAL_H = MONTH_H + WEEKS.length * MONTH_H;

// --- canvas ---
const canvas = document.getElementById("c") as HTMLCanvasElement;
canvas.width = W * DPR;
canvas.height = TOTAL_H * DPR;
canvas.style.width = `${W}px`;
canvas.style.height = `${TOTAL_H}px`;
const ctx = canvas.getContext("2d")!;
ctx.scale(DPR, DPR);

// ============================================================
// MONTH VIEW (y=0 .. MONTH_H)
// ============================================================

const LW = { major: 2.0, minor: 1.0 } as const;
const FS = { title: 24, label: 15, small: 9 } as const;
const MARGIN = 30;
const LABEL_W = 80;
const NCOLS = DAYS_IN_MONTH;
const GRID_W = 1300 - MARGIN * 2;
const COL_W = (GRID_W - LABEL_W) / NCOLS;
const CELL = Math.floor(COL_W);

function drawMonthView() {
  // ── LEFT PAGE (CW) ──
  ctx.save();
  ctx.translate(SPLIT, 0);
  ctx.rotate(Math.PI / 2);
  ctx.translate(0, 30); // shift everything down

  const gridX = MARGIN;
  const dateX = gridX + LABEL_W;

  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.font = `${FS.title}px 'IBM 3270 Semi-Condensed'`;
  ctx.fillStyle = CLR.black;
  ctx.fillText(MONTH_NAMES[MONTH], 650, 28);

  const wdY = 42;
  ctx.font = `${FS.small}px 'IBM 3270 Semi-Condensed'`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  for (let d = 0; d < NCOLS; d++) {
    const cx = dateX + d * COL_W + COL_W / 2;
    const dow = new Date(YEAR, MONTH, d + 1).getDay();
    ctx.fillStyle = dow % 6 === 0 ? CLR.red : CLR.black;
    ctx.fillText(WD_ABBR[dow], cx, wdY);
  }

  const dateY = 56;
  const R = 8;
  for (let d = 0; d < NCOLS; d++) {
    const cx = dateX + d * COL_W + COL_W / 2;
    ctx.beginPath();
    ctx.arc(cx, dateY + R, R, 0, Math.PI * 2);
    ctx.fillStyle = BASE[d].isDaytime ? CLR.yellow : CLR.blue;
    ctx.fill();
    ctx.font = `${FS.small}px 'IBM 3270 Semi-Condensed'`;
    ctx.fillStyle = BASE[d].isDaytime ? CLR.black : CLR.white;
    ctx.fillText((d + 1).toString(), cx, dateY + R);
  }

  const gridTop = 76;
  const rows = Math.floor((770 - gridTop) / CELL) - 1;
  ctx.strokeStyle = CLR.red;
  ctx.lineWidth = LW.minor;
  for (let row = 0; row < rows; row++) {
    const y = gridTop + row * CELL;
    ctx.strokeRect(gridX, y, LABEL_W, CELL);
    for (let d = 0; d < NCOLS; d++) ctx.strokeRect(dateX + d * COL_W, y, COL_W, CELL);
  }
  ctx.restore();

  // center spine
  ctx.beginPath();
  ctx.moveTo(SPLIT, 0);
  ctx.lineTo(SPLIT, MONTH_H);
  ctx.strokeStyle = CLR.red;
  ctx.lineWidth = LW.major;
  ctx.stroke();

  // ── RIGHT PAGE (CCW) ──
  ctx.save();
  ctx.translate(SPLIT, MONTH_H);
  ctx.rotate(-Math.PI / 2);

  const DW = MONTH_H,
    DH = PW;
  const pad = 24;
  const calColW = (DW - pad * 2) / 7;
  const calRowH = (DH - 60 - 16) / NUM_ROWS;

  const calGrid = getMonthGrid(YEAR, MONTH);
  while (calGrid.length % 7 !== 0) calGrid.push(null);

  ctx.font = `${FS.title}px 'IBM 3270 Semi-Condensed'`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  for (let i = 0; i < 7; i++) {
    const cx = pad + calColW * i + calColW / 2;
    ctx.fillStyle = i >= 5 ? CLR.red : CLR.black;
    ctx.fillText(DAY_NAMES[i], cx, 42);
  }

  ctx.lineWidth = LW.minor;
  for (let i = 0; i < calGrid.length; i++) {
    const col = i % 7;
    const row = Math.floor(i / 7);
    const cell = calGrid[i];
    const cx = pad + col * calColW;
    const cy = 60 + row * calRowH;

    ctx.strokeStyle = CLR.red;
    ctx.strokeRect(cx, cy, calColW, calRowH);
    if (!cell) continue;

    const dcx = cx + 12,
      dcy = cy + 14;
    const isDay = dayIsDaytime(cell.date);

    ctx.beginPath();
    ctx.arc(dcx, dcy, 8, 0, Math.PI * 2);
    ctx.fillStyle = isDay ? CLR.yellow : CLR.blue;
    ctx.fill();

    ctx.font = `${FS.small}px 'IBM 3270 Semi-Condensed'`;
    ctx.fillStyle = col >= 5 ? CLR.red : isDay ? CLR.black : CLR.white;
    ctx.fillText(cell.day.toString(), dcx, dcy);

    drawMoon(ctx, cx + calColW - 36, dcy, 8, getMoonPhase(cell.date), CLR.yellow);
    drawMoon(ctx, cx + calColW - 18, dcy, 8, getEarthPhase(cell.date), CLR.blue);
  }
  ctx.restore();
}

// ============================================================
// WEEK VIEWS — original 8-panel spread, one per week
// ============================================================

function drawWeekViews() {
  for (let wi = 0; wi < WEEKS.length; wi++) {
    const week = WEEKS[wi];
    const baseY = MONTH_H + wi * MONTH_H;
    drawOneWeek(week, baseY);
  }
}

function drawOneWeek(week: WeekSpan, baseY: number) {
  const CELL_W = PW / 2; // 390
  const CELL_H = MONTH_H / 2; // 650
  const pages = [0, PW];
  const days = week.days; // [Mon..Sun]

  // build 8-slot layout: slot 0 = mini calendar, slots 1-7 = Mon..Sun
  const slots: { label: string; date: Date | null }[] = [];
  slots.push({ label: "", date: null }); // mini calendar placeholder
  for (const d of days) {
    const dow = d.date.getDay();
    slots.push({ label: `${d.date.getDate()}`, date: d.date });
  }

  // ── CROSS LINES (red) ──
  ctx.strokeStyle = CLR.red;
  ctx.lineWidth = LW.major;
  pages.forEach((ox) => {
    ctx.beginPath();
    ctx.moveTo(ox + CELL_W, baseY);
    ctx.lineTo(ox + CELL_W, baseY + MONTH_H);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(ox, baseY + CELL_H);
    ctx.lineTo(ox + PW, baseY + CELL_H);
    ctx.stroke();
  });
  // center spine
  ctx.beginPath();
  ctx.moveTo(PW, baseY);
  ctx.lineTo(PW, baseY + MONTH_H);
  ctx.stroke();

  // ── 24-division lines on all 8 cells (1h per division) ──
  for (let slotIdx = 0; slotIdx < 8; slotIdx++) {
    const pi = Math.floor(slotIdx / 4);
    const rest = slotIdx % 4;
    const r = Math.floor(rest / 2);
    const c = rest % 2;
    const sx = pages[pi] + c * CELL_W;
    const sy = baseY + r * CELL_H;
    const step = CELL_H / 24;

    for (let div = 1; div < 24; div++) {
      const dy = sy + div * step;
      ctx.beginPath();
      ctx.moveTo(sx, dy);
      ctx.lineTo(sx + CELL_W, dy);
      if (div === 8) {
        // UTC date change (BJ 08:00 = UTC 00:00) — solid red
        ctx.strokeStyle = CLR.red;
        ctx.lineWidth = LW.minor;
      } else {
        ctx.setLineDash([0.01, 3]);
        ctx.lineCap = "round";
        ctx.strokeStyle = CLR.red;
        ctx.lineWidth = 1.0;
      }
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.lineCap = "butt";
    }
  }

  // ── DAY LABELS (with date circle background) ──
  ctx.textAlign = "left";
  for (let slotIdx = 1; slotIdx < slots.length; slotIdx++) {
    const slot = slots[slotIdx];
    if (!slot.date) continue;
    const pi = Math.floor(slotIdx / 4);
    const rest = slotIdx % 4;
    const r = Math.floor(rest / 2);
    const c = rest % 2;
    const sx = pages[pi] + c * CELL_W;
    const sy = baseY + r * CELL_H;
    const isDay = dayIsDaytime(slot.date);

    // date circle (day/night colored)
    const dcx = sx + 30,
      dcy = sy + 30;
    ctx.beginPath();
    ctx.arc(dcx, dcy, 14, 0, Math.PI * 2);
    ctx.fillStyle = isDay ? CLR.yellow : CLR.blue;
    ctx.fill();

    // date number inside circle
    ctx.fillStyle = isDay ? CLR.black : CLR.white;
    ctx.font = `${FS.label}px 'IBM 3270 Semi-Condensed'`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(slot.label, dcx, dcy);

    // moon + earth icons
    drawMoon(ctx, sx + CELL_W - 48, sy + 28, 10, getMoonPhase(slot.date), CLR.yellow);
    drawMoon(ctx, sx + CELL_W - 20, sy + 28, 10, getEarthPhase(slot.date), CLR.blue);

    // div 8: UTC date change (BJ 08:00 = UTC 00:00)
    ctx.textAlign = "left";
    const utcY = sy + CELL_H * (8 / 24);
    ctx.font = `${FS.label}px 'IBM 3270 Semi-Condensed'`;
    ctx.fillStyle = CLR.red;
    ctx.fillText(`UTC ${slot.date.getMonth() + 1}/${slot.date.getDate()}`, sx + 8, utcY - 4);
  }

  ctx.textBaseline = "alphabetic";
  ctx.textAlign = "left";
}

// ============================================================
// render
// ============================================================

ctx.fillStyle = CLR.white;
ctx.fillRect(0, 0, W, TOTAL_H);
drawMonthView();
drawWeekViews();

(window as any).savePDF = () => {
  const { jsPDF } = (window as any).jspdf;
  const pdf = new jsPDF({ orientation: "landscape", unit: "px", format: [W, TOTAL_H] });
  pdf.addImage(canvas.toDataURL("image/png"), "PNG", 0, 0, W, TOTAL_H);
  pdf.save("monthly.pdf");
};
