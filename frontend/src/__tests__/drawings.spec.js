// F07 UI: DWG-T01 Rev column, DWG-T03 hull locked on edit, DWG-T04 client PDF check, DWG-T05 sample label, DWG-04 actions
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { pdfError } from '../screens/drawings/pdf'

const REV = (rev_no, rev_status, extra = {}) => ({ rev_no, rev_status, change_desc: 'c', has_file: false, file_nm: null, author_nm: '', issue_dt: null, ...extra })
const DETAIL = (revisions, extra = {}) => ({ drawing_id: 7, drawing_no: '8001-HULL-201', drawing_nm: 'n', hull_no: '8001', block_id: null,
  discipline: 'HULL', dwg_status: revisions[0].rev_status, current_rev_no: 2, designer_emp_no: null, revisions, approvals: [],
  plans: [], available_plans: [], impacts: [], ...extra })
let detail

vi.mock('../api/client', () => ({
  api: {
    codes: vi.fn(async () => ({})),
    hulls: vi.fn(async () => [{ hull_no: '8001' }, { hull_no: '8002' }]),
    blocks: vi.fn(async () => []),
    userOptions: vi.fn(async () => [{ emp_no: 'lee.dwg', display_name: '이도면' }, { emp_no: 'admin', display_name: '관리자' }]),
    drawings: vi.fn(async () => [
      { drawing_id: 1, drawing_no: 'A', current_rev_no: 2, latest_rev_no: 3, dwg_status: 'DRAFT', link_count: 1 },
      { drawing_id: 2, drawing_no: 'B', current_rev_no: 1, latest_rev_no: 1, dwg_status: 'ISSUED', link_count: 0 }]),
    drawing: vi.fn(async () => detail),
    pdfBlob: vi.fn(async () => new Blob(['%PDF-'], { type: 'application/pdf' })),
    requestApproval: vi.fn(async () => detail),
    issueRevision: vi.fn(async () => detail),
  },
}))
vi.mock('../stores/session', () => ({ session: { user: { emp_no: 'lee.dwg' } } }))
import { api } from '../api/client'
import DrawingList from '../screens/drawings/DrawingList.vue'
import DrawingDetailModal from '../screens/drawings/DrawingDetailModal.vue'

globalThis.URL.createObjectURL = vi.fn(() => 'blob:x')
globalThis.URL.revokeObjectURL = vi.fn()
const modal = (id = 7, canWrite = true) => mount(DrawingDetailModal, { props: { drawingId: id, canWrite } })

describe('F07 drawings UI', () => {
  beforeEach(() => vi.clearAllMocks())

  it('DWG-T01 list shows CurrentRevNo and latest rev when different, filters sent', async () => {
    const w = mount(DrawingList, { props: { menu: { title: '도면 목록', can_write: true } } }); await flushPromises()
    const revs = w.findAll('[data-test=rev]').map((x) => x.text())
    expect(revs).toEqual(['Rev2 (최신 Rev3)', 'Rev1'])
    await w.find('select[name=hull_no]').setValue('8002')
    await w.find('input[name=q]').setValue('pipe')
    await w.find('[data-test=search]').trigger('click'); await flushPromises()
    expect(api.drawings).toHaveBeenLastCalledWith({ hull_no: '8002', discipline: '', status: '', q: 'pipe' })
  })

  it('DWG-T04 client PDF check (type and 30MB)', () => {
    expect(pdfError({ name: 'a.txt', type: 'text/plain', size: 1 })).toMatch('PDF')
    expect(pdfError({ name: 'a.pdf', type: '', size: 31 * 1024 * 1024 })).toMatch('30MB')
    expect(pdfError({ name: 'x', type: 'application/pdf', size: 10 })).toBe('')
  })

  it('DWG-T05 no upload -> labelled sample, never fetches a file; uploaded -> blob viewer', async () => {
    detail = DETAIL([REV(0, 'DRAFT')])
    let w = modal(); await flushPromises()
    expect(w.find('[data-test=sample]').text()).toBe('샘플 PDF (미업로드)')
    expect(w.find('[data-test=sample-box]').exists()).toBe(true)
    expect(w.find('[data-test=uploaded]').exists()).toBe(false)
    expect(api.pdfBlob).not.toHaveBeenCalled()
    detail = DETAIL([REV(0, 'DRAFT', { has_file: true, file_nm: 'a.pdf' })])
    w = modal(); await flushPromises()
    expect(w.find('[data-test=uploaded]').exists()).toBe(true)
    expect(w.find('iframe').attributes('src')).toBe('blob:x#view=FitH')
  })

  it('DWG-T03 hull select disabled and drawing no readonly on edit', async () => {
    detail = DETAIL([REV(2, 'ISSUED')])
    const w = modal(); await flushPromises()
    expect(w.find('select[name=hull_no]').attributes('disabled')).toBeDefined()
    expect(w.find('input[name=drawing_no]').attributes('readonly')).toBeDefined()
  })

  it('DWG-04 action by latest rev state: DRAFT request, APPROVED issue, ISSUED new rev form', async () => {
    detail = DETAIL([REV(3, 'DRAFT'), REV(2, 'ISSUED')])
    let w = modal(); await flushPromises()
    await w.find('[data-test=rev-action] form').trigger('submit'); await flushPromises()
    expect(api.requestApproval).toHaveBeenCalledWith(7, 3, 'lee.dwg', 'admin')
    detail = DETAIL([REV(3, 'APPROVED'), REV(2, 'ISSUED')])
    w = modal(); await flushPromises()
    await w.find('[data-test=issue]').trigger('click'); await flushPromises()
    expect(api.issueRevision).toHaveBeenCalledWith(7, 3)
    detail = DETAIL([REV(2, 'ISSUED')])
    w = modal(); await flushPromises()
    expect(w.find('input[name=change_desc]').exists()).toBe(true)
  })

  it('DWG-T10 view-only hides write actions', async () => {
    detail = DETAIL([REV(0, 'DRAFT')])
    const w = modal(7, false); await flushPromises()
    for (const sel of ['[data-test=save]', '[data-test=delete]', '[data-test=rev-action]', '[data-test=upload]', '[data-test=link-add]'])
      expect(w.find(sel).exists()).toBe(false)
  })
})

describe('SHELL-T04 drawing popup / list navigation', () => {
  it('linked plan opens the gantt of the drawing hull and closes the popup', async () => {
    detail = DETAIL([REV(2, 'ISSUED')], { hull_no: '8002', plans: [{ plan_id: 31, label: '[101] 대조립', plan_status: 'WORK', required: true, need_dt: null, plan_start_dt: '2026-10-01', plan_end_dt: '2026-10-30' }] })
    const navigate = vi.fn()
    const w = mount(DrawingDetailModal, { props: { drawingId: 7, canWrite: false }, global: { provide: { navigate } } })
    await flushPromises()
    await w.find('[data-test=links] [data-test=go-plan]').trigger('click')
    expect(navigate).toHaveBeenCalledWith('plan-gantt', '8002')
    expect(w.emitted('close')).toHaveLength(1)
  })

  it('list opened with hull param searches with that hull; re-navigation restores it', async () => {
    const { ref, nextTick } = await import('vue')
    const navRequest = ref({ seq: 0 })
    const w = mount(DrawingList, { props: { menu: { title: '도면 목록', can_write: false }, param: '8002' }, global: { provide: { navRequest } } })
    await flushPromises()
    expect(api.drawings).toHaveBeenLastCalledWith(expect.objectContaining({ hull_no: '8002' }))
    w.vm.f.hull_no = '8001'; w.vm.f.q = 'x'
    navRequest.value = { token: 'dwg-list', param: '8002', seq: 1 }; await nextTick(); await flushPromises()
    expect(api.drawings).toHaveBeenLastCalledWith({ hull_no: '8002', discipline: '', status: '', q: '' })
  })
})
