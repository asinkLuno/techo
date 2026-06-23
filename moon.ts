import * as SunCalc from "suncalc";

/** moon phase in [0,1), 0=new moon, 0.5=full moon */
export function getMoonPhase(date: Date): number {
  return SunCalc.getMoonIllumination(date).phase;
}

/** draw moon icon at (cx,cy) with radius r, phase ∈ [0,1) — stateless, pure canvas2d */
export function drawMoon(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  r: number,
  phase: number,
): void {
  phase = ((phase % 1) + 1) % 1; // normalize

  // dark disk
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fillStyle = "#ddd";
  ctx.fill();

  // lit portion
  ctx.fillStyle = "#e8c830";
  ctx.beginPath();

  if (phase <= 0.5) {
    ctx.arc(cx, cy, r, -Math.PI / 2, Math.PI / 2, false);
    const term = r - phase * 4 * r;
    if (phase <= 0.25) {
      ctx.ellipse(cx, cy, term, r, 0, Math.PI / 2, -Math.PI / 2, true);
    } else {
      ctx.ellipse(cx, cy, Math.abs(term), r, 0, Math.PI / 2, -Math.PI / 2, false);
    }
  } else {
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
