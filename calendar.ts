const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export interface DayCell {
  day: number;
  date: Date;
}

/** Monday–Sunday of the week containing `ref` */
export function getWeekDays(ref: Date): { label: string; date: Date }[] {
  const dow = ref.getDay(); // 0=Sun
  const monday = new Date(ref);
  monday.setDate(ref.getDate() - ((dow + 6) % 7));

  const days: { label: string; date: Date }[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    const label = `${DAY_NAMES[d.getDay()]} ${d.getDate()}`;
    days.push({ label, date: d });
  }
  return days;
}

/** Full month grid: weeks × 7 cells, null for padding days outside the month */
export function getMonthGrid(year: number, month: number): (DayCell | null)[] {
  const firstDow = new Date(year, month, 1).getDay(); // 0=Sun
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const cells: (DayCell | null)[] = [];
  // pad leading nulls
  for (let i = 0; i < firstDow; i++) cells.push(null);
  // actual days
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push({ day: d, date: new Date(year, month, d) });
  }
  return cells;
}

export function formatMonthYear(year: number, month: number): string {
  return `${MONTH_NAMES[month]} ${year}`;
}

export { DAY_NAMES, MONTH_NAMES };
