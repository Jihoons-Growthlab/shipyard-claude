// F03 UI: DASH-01~11 render from /api/dashboard/summary, DASH-T05 navigation targets, DASH-T06 server-capped lists, empty texts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

let summary
vi.mock('../api/client', () => ({ api: { dashboard: vi.fn(async () => summary), codes: vi.fn(async () => ({})) } }))
vi.mock('../stores/codes', () => ({ loadCodes: vi.fn(async () => {}), codeName: (g, c) => c }))
vi.mock('../stores/session', () => ({ session: { menu: [{ token: 'dwg-list', can_write: false }] } }))
vi.mock('../stores/toast', () => ({ toast: vi.fn() }))
vi.mock('../screens/drawings/DrawingDetailModal.vue', () => ({ default: { name: 'DrawingDetailModal', props: ['drawingId', 'canWrite'], template: '<div data-test="dwg-modal">{{ drawingId }}</div>' } }))
import DashboardScreen from '../screens/dashboard/DashboardScreen.vue'

const plan = (i, hull = '8001') => ({ plan_id: i, hull_no: hull, label: `[10${i}] 절단`, plan_status: 'DELAY', progress_rate: 40,
  plan_start_dt: '2026-10-01', plan_end_dt: '2026-10-10', blockers: ['8002-HULL-401'], link: { screen: 'plan-gantt', param: hull } })
const base = () => ({
  today: '2026-10-19',
  kpi: { active_hulls: { value: 4, link: { screen: 'hull-list' } }, delay_plans: { value: 7, link: { screen: 'plan-gantt' } },
    waiting_plans: { value: 0, link: { screen: 'plan-gantt' } }, pending_drawings: { value: 6, link: { screen: 'dwg-approval' } } },
  hull_progress: [{ hull_no: '8001', hull_nm: 'A', progress: 55, link: { screen: 'plan-gantt', param: '8001' } }],
  plan_status: ['PLAN', 'READY', 'WORK', 'DONE', 'DELAY'].map((s, i) => ({ status: s, count: i })),
  drawing_disciplines: [{ discipline: 'HULL', name: '선체', total: 4, counts: { ISSUED: 2, APPROVED: 1, REVIEW: 1, DRAFT: 0 } }],
  deliveries: [{ month: '2026-12', count: 2, hull_nos: ['8005', '8006'] }],
  delay_list: { count: 7, items: [1, 2, 3, 4, 5, 6].map((i) => plan(i, i === 2 ? '8002' : '8001')) },
  waiting_list: { count: 0, items: [] },
  impact_list: { count: 1, items: [{ drawing_id: 4, drawing_no: '8001-HULL-201', rev_no: 2, issue_dt: '2026-10-12', plan_id: 6,
    plan_label: '[201] 강재절단', plan_status: 'DONE', change_desc: '보강', link: { screen: 'drawing', param: 4 } }] },
})

const mk = (navigate = vi.fn()) => ({ navigate, w: mount(DashboardScreen, { props: { menu: { title: '대시보드' } }, global: { provide: { navigate } } }) })

describe('F03 dashboard', () => {
  beforeEach(() => { vi.clearAllMocks(); summary = base() })

  it('renders KPIs, charts, capped lists and empty text', async () => {
    const { w } = mk(); await flushPromises()
    expect(w.find('[data-test=kpi-delay_plans]').text()).toContain('7')
    expect(w.findAll('[data-test=delay-list] li')).toHaveLength(6) // DASH-T06
    expect(w.find('[data-test=delay-list] h3').text()).toContain('7')
    expect(w.find('[data-test=waiting-list]').text()).toContain('대기 중인 공정이 없습니다.')
    expect(w.find('[data-test=plan-status]').text()).toContain('10') // total 0+1+2+3+4
    expect(w.find('[data-test=deliveries]').text()).toContain('8005,8006')
    expect(w.findAll('[data-test=disciplines] .stk > div')).toHaveLength(3) // zero DRAFT segment omitted
  })

  it('DASH-T05 KPI/rows navigate to target screen with hull; impact opens drawing popup', async () => {
    const { w, navigate } = mk(); await flushPromises()
    await w.find('[data-test=kpi-active_hulls]').trigger('click')
    await w.find('[data-test=kpi-pending_drawings]').trigger('click')
    await w.find('[data-test=hull-progress] .hb').trigger('click')
    await w.findAll('[data-test=delay-list] li')[1].trigger('click')
    expect(navigate.mock.calls).toEqual([['hull-list', null], ['dwg-approval', null], ['plan-gantt', '8001'], ['plan-gantt', '8002']])
    await w.find('[data-test=impact-list] li').trigger('click')
    expect(w.find('[data-test=dwg-modal]').text()).toBe('4')
  })
})
