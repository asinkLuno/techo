import { getMonthGrid, MONTH_NAMES, DAY_NAMES } from "./calendar";
import { drawMoon, getMoonPhase, getEarthPhase, getTranquilityBaseStatus, LunarBaseStatus } from "./moon";
import { CLR } from "./colors";

// --- constants ---
const DPR = Math.max(window.devicePixelRatio || 1, 2);
const PW = 780;
const MONTH_H = 1300;
const W = PW * 2; // 1560
const SPLIT = PW;

const YEAR = 2026;
const WD_ABBR = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

const LW = { major: 2.0, minor: 1.0 } as const;
const FS = { title: 24, label: 15, small: 9 } as const;
const MARGIN = 30;
const LABEL_W = 80;

// --- global ctx (swapped per page during render) ---
let ctx: CanvasRenderingContext2D;

// --- per-month data ---
interface WeekSpan {
  label: string;
  days: { date: Date; inMonth: boolean }[];
}

interface MonthData {
  year: number;
  month: number;
  daysInMonth: number;
  numRows: number;
  base: LunarBaseStatus[];
  weeks: WeekSpan[];
}

function buildMonthData(year: number, month: number): MonthData {
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const numRows = Math.ceil((new Date(year, month, 1).getDay() + daysInMonth) / 7);

  const base: LunarBaseStatus[] = [];
  for (let d = 1; d <= daysInMonth; d++) {
    base.push(getTranquilityBaseStatus(new Date(year, month, d, 12)));
  }

  const weeks: WeekSpan[] = [];
  const thisFirst = new Date(year, month, 1);
  const nextFirst = new Date(year, month + 1, 1);
  const start = new Date(thisFirst);
  start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
  const end = new Date(nextFirst);
  end.setDate(end.getDate() - ((end.getDay() + 6) % 7));

  const cursor = new Date(start);
  while (cursor < end) {
    const days: WeekSpan["days"] = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(cursor);
      days.push({ date: d, inMonth: d.getMonth() === month });
      cursor.setDate(cursor.getDate() + 1);
    }
    const mon = days[0].date,
      sun = days[6].date;
    weeks.push({
      label: `${DAY_NAMES[mon.getDay()]} ${mon.getDate()} – ${DAY_NAMES[sun.getDay()]} ${sun.getDate()}`,
      days,
    });
  }

  return { year, month, daysInMonth, numRows, base, weeks };
}

const MONTHS: MonthData[] = [];
for (let m = 0; m < 12; m++) {
  MONTHS.push(buildMonthData(YEAR, m));
}

// ============================================================
// canvas factory
// ============================================================

function makeCanvas(): HTMLCanvasElement {
  const c = document.createElement("canvas");
  c.width = W * DPR;
  c.height = MONTH_H * DPR;
  c.style.width = `${W}px`;
  c.style.height = `${MONTH_H}px`;
  return c;
}

// ============================================================
// helpers
// ============================================================

function dayIsDaytime(date: Date): boolean {
  return getTranquilityBaseStatus(date).isDaytime;
}


// ============================================================
// MONTH VIEW (renders to current ctx, baseY=0)
// ============================================================

function drawMonthView(md: MonthData) {
  const { year, month, daysInMonth, numRows, base } = md;
  const NCOLS = daysInMonth;
  const GRID_W = 1300 - MARGIN * 2;
  const COL_W = (GRID_W - LABEL_W) / NCOLS;
  const CELL = Math.floor(COL_W);

  // ── LEFT PAGE (CW) ──
  ctx.save();
  ctx.translate(SPLIT, 0);
  ctx.rotate(Math.PI / 2);
  ctx.translate(0, 30);

  const gridX = MARGIN;
  const dateX = gridX + LABEL_W;

  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.font = `${FS.title}px 'IBM 3270 Semi-Condensed'`;
  ctx.fillStyle = CLR.black;
  ctx.fillText(MONTH_NAMES[month], 650, 28);

  const wdY = 42;
  ctx.font = `${FS.small}px 'IBM 3270 Semi-Condensed'`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  for (let d = 0; d < NCOLS; d++) {
    const cx = dateX + d * COL_W + COL_W / 2;
    const dow = new Date(year, month, d + 1).getDay();
    ctx.fillStyle = dow % 6 === 0 ? CLR.red : CLR.black;
    ctx.fillText(WD_ABBR[dow], cx, wdY);
  }

  const dateY = 56;
  const R = 8;
  for (let d = 0; d < NCOLS; d++) {
    const cx = dateX + d * COL_W + COL_W / 2;
    ctx.beginPath();
    ctx.arc(cx, dateY + R, R, 0, Math.PI * 2);
    ctx.fillStyle = base[d].isDaytime ? CLR.yellow : CLR.blue;
    ctx.fill();
    ctx.font = `${FS.small}px 'IBM 3270 Semi-Condensed'`;
    ctx.fillStyle = base[d].isDaytime ? CLR.black : CLR.white;
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
  ctx.fillStyle = CLR.bg;
  for (let row = 0; row <= rows; row++) {
    const y = gridTop + row * CELL;
    ctx.fillRect(gridX - 2, y - 2, 4, 4);
    for (let d = 0; d <= NCOLS; d++) {
      const cx = dateX + d * COL_W;
      ctx.fillRect(cx - 2, y - 2, 4, 4);
    }
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
  const calRowH = (DH - 60 - 16) / numRows;

  const calGrid = getMonthGrid(year, month);
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
  ctx.fillStyle = CLR.bg;
  for (let row = 0; row <= numRows; row++) {
    const cy = 60 + row * calRowH;
    for (let col = 0; col <= 7; col++) {
      const cx = pad + col * calColW;
      ctx.fillRect(cx - 2, cy - 2, 4, 4);
    }
  }
  ctx.restore();
}

// ============================================================
// WEEK VIEW (renders to current ctx, baseY=0)
// ============================================================

function drawOneWeek(week: WeekSpan) {
  const CELL_W = PW / 2;
  const CELL_H = MONTH_H / 2;
  const pages = [0, PW];

  const slots: { label: string; date: Date | null }[] = [];
  slots.push({ label: "", date: null });
  for (const d of week.days) {
    slots.push({ label: `${d.date.getDate()}`, date: d.date });
  }

  // ── CROSS LINES (red) ──
  ctx.strokeStyle = CLR.red;
  ctx.lineWidth = LW.major;
  pages.forEach((ox) => {
    ctx.beginPath();
    ctx.moveTo(ox + CELL_W, 0);
    ctx.lineTo(ox + CELL_W, MONTH_H);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(ox, CELL_H);
    ctx.lineTo(ox + PW, CELL_H);
    ctx.stroke();
  });
  ctx.beginPath();
  ctx.moveTo(PW, 0);
  ctx.lineTo(PW, MONTH_H);
  ctx.stroke();

  ctx.fillStyle = CLR.bg;
  [CELL_W, PW + CELL_W].forEach((vx) => {
    ctx.fillRect(vx - 2, CELL_H - 2, 4, 4);
  });
  ctx.fillRect(PW - 2, CELL_H - 2, 4, 4);

  // ── 24-division lines ──
  for (let slotIdx = 0; slotIdx < 8; slotIdx++) {
    const pi = Math.floor(slotIdx / 4);
    const rest = slotIdx % 4;
    const r = Math.floor(rest / 2);
    const c = rest % 2;
    const sx = pages[pi] + c * CELL_W;
    const sy = r * CELL_H;
    const step = CELL_H / 24;

    for (let div = 1; div < 24; div++) {
      const dy = sy + div * step;
      ctx.beginPath();
      ctx.moveTo(sx, dy);
      ctx.lineTo(sx + CELL_W, dy);
      if (div === 8) {
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

  // cover UTC line × cross line intersections
  ctx.fillStyle = CLR.bg;
  [CELL_W, PW, PW + CELL_W].forEach((vx) => {
    for (let r = 0; r < 2; r++) {
      const uy = r * CELL_H + CELL_H * (8 / 24);
      ctx.fillRect(vx - 2, uy - 2, 4, 4);
    }
  });

  // ── DAY LABELS ──
  ctx.textAlign = "left";
  for (let slotIdx = 1; slotIdx < slots.length; slotIdx++) {
    const slot = slots[slotIdx];
    if (!slot.date) continue;
    const pi = Math.floor(slotIdx / 4);
    const rest = slotIdx % 4;
    const r = Math.floor(rest / 2);
    const c = rest % 2;
    const sx = pages[pi] + c * CELL_W;
    const sy = r * CELL_H;
    const isDay = dayIsDaytime(slot.date);

    const dcx = sx + 30,
      dcy = sy + 30;
    ctx.beginPath();
    ctx.arc(dcx, dcy, 14, 0, Math.PI * 2);
    ctx.fillStyle = isDay ? CLR.yellow : CLR.blue;
    ctx.fill();

    ctx.fillStyle = isDay ? CLR.black : CLR.white;
    ctx.font = `${FS.label}px 'IBM 3270 Semi-Condensed'`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(slot.label, dcx, dcy);

    drawMoon(ctx, sx + CELL_W - 48, sy + 28, 10, getMoonPhase(slot.date), CLR.yellow);
    drawMoon(ctx, sx + CELL_W - 20, sy + 28, 10, getEarthPhase(slot.date), CLR.blue);

    // div 8: UTC date change (BJ 08:00 = UTC 00:00)
    ctx.textAlign = "left";
    const utcY = sy + CELL_H * (8 / 24);
    ctx.font = `${FS.label}px 'IBM 3270 Semi-Condensed'`;
    ctx.fillStyle = CLR.red;
    ctx.fillText(`UTC ${slot.date.getDate()}`, sx + 8, utcY - 6);
  }

  ctx.textBaseline = "alphabetic";
  ctx.textAlign = "left";
}

// ============================================================
// render all pages into separate canvases
// ============================================================

const container = document.getElementById("pages")!;

function render() {
  for (const md of MONTHS) {
    // month view
    const mc = makeCanvas();
    ctx = mc.getContext("2d")!;
    ctx.scale(DPR, DPR);
    ctx.fillStyle = CLR.bg;
    ctx.fillRect(0, 0, W, MONTH_H);
    drawMonthView(md);

    container.appendChild(mc);

    // week views
    for (const week of md.weeks) {
      const wc = makeCanvas();
      ctx = wc.getContext("2d")!;
      ctx.scale(DPR, DPR);
      ctx.fillStyle = CLR.bg;
      ctx.fillRect(0, 0, W, MONTH_H);
      drawOneWeek(week);
  
      container.appendChild(wc);
    }
  }
}

render();

// ============================================================
// PDF export (browser, using jsPDF)
// ============================================================

(window as any).savePDF = () => {
  const { jsPDF } = (window as any).jspdf;
  const pdf = new jsPDF({ orientation: "landscape", unit: "px", format: [W, MONTH_H] });
  const tmp = makeCanvas();
  const tctx = tmp.getContext("2d")!;
  tctx.scale(DPR, DPR);

  let first = true;
  for (const md of MONTHS) {
    ctx = tctx;
    ctx.fillStyle = CLR.bg;
    ctx.fillRect(0, 0, W, MONTH_H);
    drawMonthView(md);

    if (!first) pdf.addPage([W, MONTH_H]);
    first = false;
    pdf.addImage(tmp.toDataURL("image/png"), "PNG", 0, 0, W, MONTH_H);

    for (const week of md.weeks) {
      ctx.fillStyle = CLR.bg;
      ctx.fillRect(0, 0, W, MONTH_H);
      drawOneWeek(week);
  
      pdf.addPage([W, MONTH_H]);
      pdf.addImage(tmp.toDataURL("image/png"), "PNG", 0, 0, W, MONTH_H);
    }
  }

  pdf.save("2026.pdf");
};
