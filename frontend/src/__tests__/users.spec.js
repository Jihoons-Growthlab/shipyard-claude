// F09 UI: USR-T01 filter/reset + top-bottom selection, USR-02 new defaults & payload, USR-T03 blank password, USR-03 approve/self-delete
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const U = (emp_no, status = 'approved', groups = [{ code: 'VIEW', name: '조회전용' }]) => ({ emp_no, last_name: '김', first_name: emp_no,
  display_name: '김' + emp_no, email: `${emp_no}@x.kr`, phone: '010-1111-2222', birth_date: '1990-01-01', status, totp_enabled: false, groups, created_at: '2026-01-05' })
vi.mock('../api/client', () => ({
  api: {
    users: vi.fn(async () => ({ users: [U('admin'), U('jung.new', 'pending', [])], total: 2, pending: 1 })),
    authGroups: vi.fn(async () => [{ code: 'VIEW', name: '조회전용' }, { code: 'DWG', name: '도면관리자' }]),
    createUser: vi.fn(async (b) => U(b.emp_no)),
    updateUser: vi.fn(async (emp) => U(emp)),
    deleteUser: vi.fn(async () => null),
    approveUser: vi.fn(async () => ({})),
  },
}))
vi.mock('../stores/session', () => ({ session: { user: { emp_no: 'admin' }, load: vi.fn(async () => {}) } }))
vi.mock('../stores/toast', () => ({ toast: vi.fn() }))
import { api } from '../api/client'
import { session } from '../stores/session'
import { toast } from '../stores/toast'
import UserManagement from '../screens/users/UserManagement.vue'

const mk = () => mount(UserManagement, { props: { menu: { title: '회원관리', can_write: true } } })

describe('F09 user management', () => {
  beforeEach(() => vi.clearAllMocks())

  it('USR-T01 filter, reset, counts and row selection fills bottom form', async () => {
    const w = mk(); await flushPromises()
    expect(w.find('[data-test=counts]').text()).toBe('2명 · 승인대기 1명')
    await w.find('select[name=status]').setValue('pending'); await w.find('input[name=q]').setValue('jung')
    await w.find('[data-test=search]').trigger('click'); await flushPromises()
    expect(api.users).toHaveBeenLastCalledWith({ status: 'pending', q: 'jung' })
    await w.find('[data-test=reset]').trigger('click'); await flushPromises()
    expect(api.users).toHaveBeenLastCalledWith({ status: '', q: '' })
    await w.find('tr[data-id="admin"]').trigger('click')
    expect(w.find('input[name=emp_no]').element.value).toBe('admin')
    expect(w.find('input[name=emp_no]').attributes('readonly')).toBeDefined()
  })

  it('USR-02 new form defaults and create payload', async () => {
    const w = mk(); await flushPromises()
    await w.find('[data-test=new]').trigger('click')
    expect(w.vm.f.status).toBe('approved'); expect(w.vm.f.totp_enabled).toBe(false)
    await w.find('input[name=emp_no]').setValue('kim.new'); await w.find('input[name=password]').setValue('pass1234')
    await w.find('[data-test=save]').trigger('click'); await flushPromises()
    expect(api.createUser).toHaveBeenCalledWith(expect.objectContaining({ emp_no: 'kim.new', password: 'pass1234', status: 'approved', group: null }))
  })

  it('USR-T03 edit sends blank password; self edit reloads header/menu', async () => {
    const w = mk(); await flushPromises()
    await w.find('tr[data-id="admin"]').trigger('click')
    await w.find('[data-test=save]').trigger('click'); await flushPromises()
    expect(api.updateUser).toHaveBeenCalledWith('admin', expect.objectContaining({ password: '', group: 'VIEW' }))
    expect(session.load).toHaveBeenCalled()
  })

  it('USR-03 self delete blocked client-side; pending shows approve with selected group', async () => {
    const w = mk(); await flushPromises()
    await w.find('tr[data-id="admin"]').trigger('click')
    await w.find('[data-test=delete]').trigger('click')
    expect(api.deleteUser).not.toHaveBeenCalled()
    expect(toast).toHaveBeenCalledWith('로그인 중인 본인 계정은 삭제할 수 없습니다.', 'e')
    expect(w.find('[data-test=approve]').exists()).toBe(false)
    await w.find('tr[data-id="jung.new"]').trigger('click')
    await w.find('select[name=group]').setValue('DWG')
    await w.find('[data-test=approve]').trigger('click'); await flushPromises()
    expect(api.approveUser).toHaveBeenCalledWith('jung.new', ['DWG'])
  })
})
