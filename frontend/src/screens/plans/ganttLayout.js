// PLAN-01 timeline math (mirrors mockup `gantt`): range = plans ∪ [TODAY-5, TODAY+5], snapped to month start, +8 days pad.
export const ZOOMS = [{ v: 2.5, label: '축소' }, { v: 4, label: '보통' }, { v: 6, label: '확대' }]
export const LABEL_W = 230
export const ROW_H = 28
const DAY = 864e5
export const dayNo = (iso) => Date.parse(iso + 'T00:00:00Z') / DAY

export function layout(plans, today, ppd = 4) {
  const t = dayNo(today)
  let min = Math.min(t - 5, ...plans.map((p) => dayNo(p.plan_start_dt)))
  const max = Math.max(t + 5, ...plans.map((p) => dayNo(p.plan_end_dt)))
  const d0 = new Date(min * DAY)
  min = Date.UTC(d0.getUTCFullYear(), d0.getUTCMonth(), 1) / DAY
  const total = max - min + 8
  const pct = (n) => (n / total) * 100
  const months = []
  for (let y = d0.getUTCFullYear(), m = d0.getUTCMonth(); ; m++) {
    if (m > 11) { m = 0; y++ }
    const a = Date.UTC(y, m, 1) / DAY, b = Date.UTC(y, m + 1, 1) / DAY
    if (a > max + 5) break
    months.push({ label: `${y}.${String(m + 1).padStart(2, '0')}`, left: pct(a - min), width: pct(b - a) })
  }
  const bars = Object.fromEntries(plans.map((p) => [p.plan_id, {
    left: pct(dayNo(p.plan_start_dt) - min),
    width: pct(dayNo(p.plan_end_dt) - dayNo(p.plan_start_dt) + 1),
  }]))
  return {
    min, total, months, bars,
    width: LABEL_W + Math.ceil(total * ppd),
    todayPct: pct(t - min),
    ux: (iso, plusOne = 0) => ((dayNo(iso) + plusOne - min) / total) * 1000, // SVG viewBox 0..1000
  }
}

// Initial horizontal scroll: TODAY line at ~40% of the visible width.
export function initialScroll(lay, clientWidth) {
  const todayX = LABEL_W + (lay.todayPct / 100) * (lay.width - LABEL_W)
  return Math.max(0, todayX - clientWidth * 0.4)
}
