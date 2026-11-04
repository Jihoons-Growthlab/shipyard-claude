// F05 UI: PLAN-T01 (filters/zoom/today line/scroll restore), PLAN-T04 (late predecessor confirm), PLAN-T08 marker
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { layout, initialScroll, LABEL_W } from '../screens/plans/ganttLayout'

const P = (id, block_id, block_cd, s, e, extra = {}) => ({
  plan_id: id, block_id, block_cd, proc_cd: 'CUT', proc_nm: '강재절단', label: `[${block_cd ?? '호선'}] 강재절단`,
  plan_start_dt: s, plan_end_dt: e, progress_rate: 0, plan_status: 'PLAN', pred_plan_ids: [], drawing_wait: false, ...extra,
})
const PLANS = [P(1, 10, '101', '2026-09-01', '2026-09-30', { plan_status: 'DONE', progress_rate: 100 }),
  P(2, 10, '101', '2026-10-01', '2026-11-15', { pred_plan_ids: [1] }),
  P(3, 20, '201', '2026-10-20', '2026-12-31', { drawing_wait: true })]
const LATE = Object.assign(new Error('선행 공정 종료일이 이 공정의 시작일보다 늦습니다. 그대로 저장할까요?'), { code: 'PRED_LATE_CONFIRM_REQUIRED', status: 409 })

vi.mock('../stores/session', () => ({ session: { menu: [] } }))
vi.mock('../screens/drawings/DrawingDetailModal.vue', () => ({ default: { name: 'DrawingDetailModal', template: '<div />' } }))
vi.mock('../api/client', () => ({
  api: {
    codes: vi.fn(async () => ({ PLANSTAT: [{ code: 'PLAN', name: '계획' }, { code: 'DONE', name: '완료' }] })),
    planHulls: vi.fn(async () => [{ hull_no: '8004', plan_count: 0 }, { hull_no: '8001', plan_count: 3 }, { hull_no: '8002', plan_count: 1 }]),
    procs: vi.fn(async () => [{ proc_cd: 'CUT', proc_nm: '강재절단' }]),
    userOptions: vi.fn(async () => []),
    plans: vi.fn(async (no) => ({ hull_no: no, hull_progress: 40, today: '2026-10-19', plans: PLANS,
      deps: [{ plan_id: 2, pred_plan_id: 1, lag_days: 0 }] })),
    blocks: vi.fn(async () => [{ block_id: 10, block_cd: '101' }, { block_id: 20, block_cd: '201' }]),
    planDrawings: vi.fn(async () => ({ blockers: [], links: [], available: [] })),
    createPlan: vi.fn(), updatePlan: vi.fn(),
  },
}))
import { api } from '../api/client'
import PlanGantt from '../screens/plans/PlanGantt.vue'
import PlanPanel from '../screens/plans/PlanPanel.vue'

beforeEach(() => vi.clearAllMocks())

describe('PLAN-T01 layout', () => {
  it('range snaps to month start, today line position, zoom scales width', () => {
    const l = layout(PLANS, '2026-10-19', 4)
    expect(l.months[0].label).toBe('2026.09')
    expect(l.months.map((m) => m.label)).toContain('2026.12')
    const start = Date.UTC(2026, 8, 1) / 864e5, today = Date.UTC(2026, 9, 19) / 864e5, end = Date.UTC(2026, 11, 31) / 864e5
    expect(l.total).toBe(end - start + 8)
    expect(l.todayPct).toBeCloseTo(((today - start) / l.total) * 100, 6)
    expect(l.width).toBe(LABEL_W + Math.ceil(l.total * 4))
    expect(layout(PLANS, '2026-10-19', 6).width).toBeGreaterThan(l.width)
    expect(layout(PLANS, '2026-10-19', 2.5).width).toBeLessThan(l.width)
    const todayX = LABEL_W + (l.todayPct / 100) * (l.width - LABEL_W)
    expect(initialScroll(l, 500)).toBeCloseTo(todayX - 200, 6) // today at 40% of viewport
  })
  it('empty plan list still shows TODAY±5 window', () => {
    const l = layout([], '2026-10-19', 4)
    expect(l.todayPct).toBeGreaterThan(0)
  })
})

describe('PLAN-T01 gantt screen', () => {
  const menu = { title: '공정 계획', token: 'plan-gantt', can_write: true }
  it('defaults to first hull with plans, filters by block, keeps whole-hull progress, marks drawing wait', async () => {
    const w = mount(PlanGantt, { props: { menu }, attachTo: document.body })
    await flushPromises()
    expect(api.plans).toHaveBeenCalledWith('8001')
    expect(w.findAll('[data-plan]')).toHaveLength(3)
    expect(w.findAll('path')).toHaveLength(1)
    expect(w.findAll('[data-test=dwg-wait]')).toHaveLength(1)
    await w.find('select[name=block]').setValue('20')
    expect(w.findAll('[data-plan]').map((r) => r.attributes('data-plan'))).toEqual(['3'])
    expect(w.findAll('path')).toHaveLength(0)
    expect(w.find('[data-test=hull-progress]').text()).toContain('40%')
    // select -> panel; hull change resets block/selection
    await w.find('[data-plan="3"]').trigger('click'); await flushPromises()
    expect(w.find('[data-test=plan-panel]').exists()).toBe(true)
    await w.find('select[name=hull]').setValue('8002'); await flushPromises()
    expect(w.vm.s.block).toBe('')
    expect(w.vm.s.sel).toBe(null)
    expect(api.plans).toHaveBeenLastCalledWith('8002')
    w.unmount()
  })
  it('linked drawing number in the panel opens the drawing popup', async () => {
    api.planDrawings.mockResolvedValueOnce({ blockers: [], available: [], links: [{ drawing_id: 9, drawing_no: 'D-9', dwg_status: 'ISSUED', has_issued: true, required: true }] })
    const w = mount(PlanGantt, { props: { menu }, attachTo: document.body })
    await flushPromises()
    await w.find('[data-plan="3"]').trigger('click'); await flushPromises()
    expect(w.findComponent({ name: 'DrawingDetailModal' }).exists()).toBe(false)
    await w.find('[data-test=open-drawing]').trigger('click')
    expect(w.findComponent({ name: 'DrawingDetailModal' }).exists()).toBe(true)
    w.unmount()
  })
  it('restores horizontal scroll after a reload (save)', async () => {
    const w = mount(PlanGantt, { props: { menu }, attachTo: document.body })
    await flushPromises()
    const g = w.vm.scroller
    Object.defineProperty(g, 'clientWidth', { value: 400, configurable: true })
    g.scrollLeft = 123
    await g.dispatchEvent(new Event('scroll'))
    await w.find('[data-plan="2"]').trigger('click')
    await w.vm.$.setupState.onSaved(2)
    await flushPromises()
    expect(g.scrollLeft).toBe(123)
    w.unmount()
  })
})

describe('PLAN-T04 late predecessor confirmation', () => {
  const props = { plan: PLANS[1], hullNo: '8001', today: '2026-10-19', allPlans: PLANS, blocks: [], procs: [{ proc_cd: 'CUT', proc_nm: '강재절단' }], users: [], canWrite: true }
  it('cancel sends nothing more; confirm resends with confirm_late_preds', async () => {
    api.updatePlan.mockRejectedValueOnce(LATE)
    const conf = vi.spyOn(window, 'confirm').mockReturnValueOnce(false)
    const w = mount(PlanPanel, { props })
    await flushPromises()
    await w.find('[data-test=plan-form]').trigger('submit'); await flushPromises()
    expect(conf).toHaveBeenCalledOnce()
    expect(api.updatePlan).toHaveBeenCalledTimes(1)
    expect(w.emitted('saved')).toBeUndefined()

    api.updatePlan.mockRejectedValueOnce(LATE).mockResolvedValueOnce({ plan_id: 2 })
    conf.mockReturnValueOnce(true)
    await w.find('[data-test=plan-form]').trigger('submit'); await flushPromises()
    expect(api.updatePlan).toHaveBeenCalledTimes(3)
    expect(api.updatePlan.mock.calls[2][1].confirm_late_preds).toBe(true)
    expect(w.emitted('saved')[0]).toEqual([2])
    conf.mockRestore()
  })
  it('new plan defaults: CUT, TODAY~TODAY+13, selected block', async () => {
    const w = mount(PlanPanel, { props: { ...props, plan: null, defaultBlockId: null } })
    expect(w.find('input[name=plan_start_dt]').element.value).toBe('2026-10-19')
    expect(w.find('input[name=plan_end_dt]').element.value).toBe('2026-11-01')
    expect(w.find('select[name=proc_cd]').element.value).toBe('CUT')
  })
})

describe('DASH-T05 / SHELL-T04 gantt hull context', () => {
  it('param selects that hull on open; re-navigation to a reused tab restores it', async () => {
    const { ref, nextTick } = await import('vue')
    const navRequest = ref({ seq: 0 })
    const w = mount(PlanGantt, { props: { menu: { title: '공정 계획', can_write: false }, param: '8002' }, global: { provide: { navRequest } } })
    await flushPromises()
    expect(api.plans).toHaveBeenLastCalledWith('8002')
    await w.find('select[name=hull]').setValue('8001'); await flushPromises()
    expect(api.plans).toHaveBeenLastCalledWith('8001')
    navRequest.value = { token: 'plan-gantt', param: '8002', seq: 1 }; await nextTick(); await flushPromises()
    expect(w.find('select[name=hull]').element.value).toBe('8002')
    expect(api.plans).toHaveBeenLastCalledWith('8002')
  })

  it('unknown param falls back to the first hull with plans', async () => {
    mount(PlanGantt, { props: { menu: { title: '공정 계획', can_write: false }, param: '9999' } })
    await flushPromises()
    expect(api.plans).toHaveBeenLastCalledWith('8001')
  })
})
