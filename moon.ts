import * as SunCalc from "suncalc";

const C = 299792.458; // speed of light, km/s

/** moon phase in [0,1), 0=new moon, 0.5=full moon */
export function getMoonPhase(date: Date): number {
  return SunCalc.getMoonIllumination(date).phase;
}

/** earth phase as seen from the moon — half-cycle offset from moon phase */
export function getEarthPhase(date: Date): number {
  return (SunCalc.getMoonIllumination(date).phase + 0.5) % 1;
}

/** Chinese moon phase name from phase value */
export function getMoonPhaseName(phase: number): string {
  phase = ((phase % 1) + 1) % 1;
  if (phase < 0.03 || phase > 0.97) return "新月(朔)";
  if (Math.abs(phase - 0.25) < 0.03) return "上弦月";
  if (Math.abs(phase - 0.5) < 0.03) return "满月(望)";
  if (Math.abs(phase - 0.75) < 0.03) return "下弦月";
  if (phase > 0.03 && phase < 0.25) return "蛾眉月";
  if (phase > 0.25 && phase < 0.5) return "盈凸月";
  if (phase > 0.5 && phase < 0.75) return "亏凸月";
  return "残月";
}

// --- Tranquility Base environmental model ---

/**
 * Environmental status at Mare Tranquillitatis (静海基地).
 * Uses SunCalc's moon phase as an absolute time reference, then maps it
 * via trig to the Sun altitude at the landing site.
 */
export interface LunarBaseStatus {
  date: string;
  phase: number; // raw moon phase [0,1)
  moonPhaseName: string;
  earthFraction: number; // 0-100
  sunAltitude: number; // degrees
  isDaytime: boolean;
  baseTemperature: number; // °C
  evaSafety: string;
}

export function getTranquilityBaseStatus(date: Date): LunarBaseStatus {
  const illum = SunCalc.getMoonIllumination(date);
  const phase = illum.phase;

  // Sun altitude at Tranquility: cos() maps phase [0,1] → altitude [-90°, 90°]
  // Full moon (0.5) = noon (90°), New moon (0/1) = midnight (-90°)
  const sunAltRad = Math.cos((phase - 0.5) * 2 * Math.PI) * (Math.PI / 2);
  const sunAltitude = sunAltRad * (180 / Math.PI);

  // Earth fraction = complement of moon fraction
  const earthFraction = (1 - illum.fraction) * 100;

  const isDaytime = sunAltitude > 0;
  let temperature = -130;
  let evaSafety = "🔴 极寒禁出";

  if (isDaytime) {
    temperature = 20 + (sunAltitude / 90) * 100;
    if (sunAltitude > 75) evaSafety = "🟡 正午强辐射";
    else if (sunAltitude < 15) evaSafety = "🟠 晨昏温变";
    else evaSafety = "🟢 适宜作业";
  }

  return {
    date: date.toISOString(),
    phase,
    moonPhaseName: getMoonPhaseName(phase),
    earthFraction: Math.round(earthFraction * 10) / 10,
    sunAltitude: Math.round(sunAltitude * 100) / 100,
    isDaytime,
    baseTemperature: Math.round(temperature),
    evaSafety,
  };
}

/** round-trip Earth–Moon light-time delay in milliseconds */
export function getMoonDelay(date: Date, lat: number, lng: number): number {
  const { distance } = SunCalc.getMoonPosition(date, lat, lng);
  return (2 * distance / C) * 1000;
}

/** hourly moon altitudes (radians) for a 24h day at given location */
export function getHourlyAltitudes(date: Date, lat: number, lng: number): number[] {
  const alts: number[] = [];
  const base = new Date(date);
  for (let h = 0; h < 24; h++) {
    const t = new Date(base);
    t.setHours(h, 0, 0, 0);
    alts.push(SunCalc.getMoonPosition(t, lat, lng).altitude);
  }
  return alts;
}

/** moon delays for each noon (UTC) of a month */
export function getMonthDelays(year: number, month: number, lat: number, lng: number): number[] {
  const days = new Date(year, month + 1, 0).getDate();
  const delays: number[] = [];
  for (let d = 1; d <= days; d++) {
    delays.push(getMoonDelay(new Date(Date.UTC(year, month, d, 12)), lat, lng));
  }
  return delays;
}

/** draw moon/planet icon at (cx,cy) with radius r, phase ∈ [0,1) — lit fill + colored outline, no dark fill */
export function drawMoon(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  r: number,
  phase: number,
  litColor = "#e8c830",
): void {
  phase = ((phase % 1) + 1) % 1; // normalize

  // lit portion (filled)
  ctx.fillStyle = litColor;
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

  // colored outline
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.strokeStyle = litColor;
  ctx.lineWidth = 0.8;
  ctx.stroke();
}
