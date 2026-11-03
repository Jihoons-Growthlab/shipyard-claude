// F06 UI: PROG-T01 (default hull/active list, include-done toggle), PROG-02 form defaults + save payload, PROG-T06 readonly
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const T = (id, st, rate = 0) => ({ plan_id: id, label: `[101] P${id}`, plan_start_dt: '2026-10-01', plan_end_dt: '2026-10-30',
  actual_start_dt: null, progress_rate: rate, plan_status: st, manager_nm: '' })
const DETAIL = { plan: { plan_id: 2, label: '[101] P2', plan_status: 'WORK', progress_rate: 40 },
  history: [{ progress_id: 9, work_dt: '2026-10-18', progress_rate: 40, man_hour: 8, worker_cnt: 2, worker_nm: '한현장', remark: null }] }

vi.mock('../api/client', () => ({
  api: {
    codes: vi.fn(async () => ({ PLANSTAT: [{ code: 'WORK', name: '진행' }] })),
    progressHulls: vi.fn(async () => ({ hulls: [{ hull_no: '8001', hull_nm: 'A' }, { hull_no: '8002', hull_nm: 'B' }], default_hull_no: '8002' })),
    userOptions: vi.fn(async () => [{ emp_no: 'park.pm', display_name: '박공정' }]),
    progressTargets: vi.fn(async (no, all) => ({ hull_no: no, today: '2026-10-19',
      plans: all ? [T(1, 'DONE', 100), T(2, 'WORK', 40)] : [T(2, 'WORK', 40)] })),
    planProgress: vi.fn(async () => DETAIL),
    saveProgress: vi.fn(async () => DETAIL),
    deleteProgress: vi.fn(async () => ({ ...DETAIL, history: [] })),
  },
}))
vi.mock('../stores/session', () => ({ session: { user: { emp_no: 'park.pm' } } }))
import { api } from '../api/client'
import ProgressScreen from '../screens/progress/ProgressScreen.vue'

const mk = (can_write = true) => mount(ProgressScreen, { props: { menu: { title: '공정 실적', can_write } } })

describe('F06 progress screen', () => {
  beforeEach(() => vi.clearAllMocks())

  it('PROG-T01 default hull, active list, include-done toggle', async () => {
    const w = mk(); await flushPromises()
    expect(api.progressTargets).toHaveBeenLastCalledWith('8002', false)
    expect(w.findAll('[data-test=targets] tbody tr[data-plan]')).toHaveLength(1)
    await w.find('input[name=showDone]').setValue(true); await flushPromises()
    expect(api.progressTargets).toHaveBeenLastCalledWith('8002', true)
    expect(w.findAll('[data-test=targets] tbody tr[data-plan]')).toHaveLength(2)
  })

  it('PROG-02 select plan -> defaults (TODAY, current rate, login user) and save payload', async () => {
    const w = mk(); await flushPromises()
    await w.find('tr[data-plan="2"]').trigger('click'); await flushPromises()
    expect(w.find('input[name=work_dt]').element.value).toBe('2026-10-19')
    expect(w.find('input[name=work_dt]').attributes('max')).toBe('2026-10-19')
    expect(w.vm.f.progress_rate).toBe(40)
    expect(w.vm.f.worker_emp_no).toBe('park.pm')
    expect(w.findAll('[data-test=history] tbody tr')).toHaveLength(1)
    await w.find('input[name=progress_rate]').setValue('100')
    await w.find('form').trigger('submit'); await flushPromises()
    expect(api.saveProgress).toHaveBeenCalledWith(2, '2026-10-19', { progress_rate: 100, man_hour: null, worker_cnt: null,
      worker_emp_no: 'park.pm', remark: null })
  })

  it('PROG-T06 view-only hides form and delete', async () => {
    const w = mk(false); await flushPromises()
    await w.find('tr[data-plan="2"]').trigger('click'); await flushPromises()
    expect(w.find('[data-test=readonly]').exists()).toBe(true)
    expect(w.find('form').exists()).toBe(false)
    expect(w.find('[data-test=history] button').exists()).toBe(false)
  })
})
