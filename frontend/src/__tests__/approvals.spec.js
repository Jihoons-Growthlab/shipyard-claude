// F08 UI: APV-01 waiting list, APV-02 reject comment required + decision payload, APV-03 issue button (can_issue), APV-T06 empty history
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

let inbox, hist
vi.mock('../api/client', () => ({
  api: {
    approvalInbox: vi.fn(async () => inbox),
    approvalHistory: vi.fn(async () => hist),
    decideApproval: vi.fn(async () => ({})),
    issueRevision: vi.fn(async () => ({})),
  },
}))
vi.mock('../stores/session', () => ({ session: { user: { emp_no: 'admin', display_name: '관리자' } } }))
vi.mock('../stores/toast', () => ({ toast: vi.fn() }))
import { api } from '../api/client'
import { toast } from '../stores/toast'
import ApprovalInbox from '../screens/approvals/ApprovalInbox.vue'

const mk = (can_write = true) => mount(ApprovalInbox, { props: { menu: { title: '결재함', can_write } } })

describe('F08 approval inbox', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    inbox = { waiting: [{ approval_id: 50, drawing_id: 9, drawing_no: '8002-HULL-401', drawing_nm: 'n', rev_no: 0, step_no: 2, change_desc: 'c' }],
      ready: [{ drawing_id: 3, drawing_no: '8003-HULL-101', drawing_nm: 'm', rev_no: 0, effect_plans: ['[101] 절단'] }], can_issue: true }
    hist = [{ approval_id: 1, act_dt: '2026-10-17 16:00', drawing_no: 'X', rev_no: 0, step_no: 1, approver_nm: '이도면', result: 'APPROVE', comment: '승인' }]
  })

  it('APV-01/03 renders waiting, ready with effect plans, history', async () => {
    const w = mk(); await flushPromises()
    expect(w.findAll('[data-test=waiting] tr[data-id]')).toHaveLength(1)
    expect(w.find('[data-test=waiting]').text()).toContain('승인')
    expect(w.find('[data-test=ready]').text()).toContain('[101] 절단')
    expect(w.findAll('[data-test=history] tbody tr')).toHaveLength(1)
  })

  it('APV-02 reject requires comment; approve sends payload', async () => {
    const w = mk(); await flushPromises()
    await w.find('[data-test=reject]').trigger('click'); await flushPromises()
    expect(api.decideApproval).not.toHaveBeenCalled()
    expect(toast).toHaveBeenCalledWith('반려 시 의견을 입력하세요.', 'e')
    await w.find('input[name=comment]').setValue('치수 오류')
    await w.find('[data-test=reject]').trigger('click'); await flushPromises()
    expect(api.decideApproval).toHaveBeenCalledWith(50, 'REJECT', '치수 오류')
    await w.find('[data-test=approve]').trigger('click'); await flushPromises()
    expect(api.decideApproval).toHaveBeenLastCalledWith(50, 'APPROVE', '')
  })

  it('APV-03 issue button only with can_issue; M33 View hides decisions', async () => {
    let w = mk(); await flushPromises()
    await w.find('[data-test=issue]').trigger('click'); await flushPromises()
    expect(api.issueRevision).toHaveBeenCalledWith(3, 0)
    inbox.can_issue = false
    w = mk(false); await flushPromises()
    expect(w.find('[data-test=issue]').exists()).toBe(false)
    expect(w.find('[data-test=approve]').exists()).toBe(false)
  })

  it('APV-T06 empty history message', async () => {
    hist = []
    const w = mk(); await flushPromises()
    expect(w.find('[data-test=history-empty]').text()).toBe('결재 이력이 없습니다.')
  })
})
