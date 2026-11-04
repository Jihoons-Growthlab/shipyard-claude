// F04 UI: HULL-T01 (filters/reset/double-click detail) and HULL-T04 (sub tab kept after save, list refresh)
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

vi.mock('../api/client', () => ({
  api: {
    codes: vi.fn(async () => ({
      HULLSTAT: [{ code: 'BUILD', name: '건조' }, { code: 'PLAN', name: '계획' }],
      SHIPTYPE: [{ code: 'LNG', name: 'LNG운반선' }], BLOCKTYPE: [{ code: 'FLAT', name: '평블록' }],
    })),
    hulls: vi.fn(async () => [
      { hull_no: '8001', hull_nm: 'A', ship_type: 'LNG', hull_status: 'BUILD', progress: null, delay_count: 0 },
      { hull_no: '8002', hull_nm: 'B', ship_type: 'LNG', hull_status: 'BUILD', progress: 42, delay_count: 2 },
    ]),
    hull: vi.fn(async (no) => ({ hull_no: no, hull_nm: 'A', hull_status: 'BUILD', use_yn: true })),
    blocks: vi.fn(async () => [{ block_id: 1, block_cd: '101', block_nm: 'x', plan_count: 0, drawing_count: 0, progress: null }]),
    addBlock: vi.fn(async () => ({})),
    milestones: vi.fn(async () => []),
    hullSummary: vi.fn(async () => ({ plan_count: 0, drawing_count: 0 })),
  },
}))

import { api } from '../api/client'
import HullList from '../screens/hulls/HullList.vue'
import HullDetailModal from '../screens/hulls/HullDetailModal.vue'

const menu = { menu_id: 'M11', title: '호선 목록', token: 'hull-list', can_write: true }
beforeEach(() => vi.clearAllMocks())

describe('HULL-T01 list', () => {
  it('sends combined filters, resets, shows 계획 없음', async () => {
    const w = mount(HullList, { props: { menu }, attachTo: document.body })
    await flushPromises()
    expect(w.text()).toContain('계획 없음')
    expect(w.text()).toContain('42%')
    await w.find('select[name=status]').setValue('BUILD')
    await w.find('select[name=ship_type]').setValue('LNG')
    await w.find('input[name=q]').setValue('nordic')
    await w.find('form.bar').trigger('submit')
    expect(api.hulls).toHaveBeenLastCalledWith({ status: 'BUILD', ship_type: 'LNG', q: 'nordic' })
    await w.find('[data-test=reset]').trigger('click')
    expect(api.hulls).toHaveBeenLastCalledWith({ status: '', ship_type: '', q: '' })
    expect(w.find('input[name=q]').element.value).toBe('')
    w.unmount()
  })

  it('double-click opens the detail popup; View-only hides 호선 등록', async () => {
    const w = mount(HullList, { props: { menu }, attachTo: document.body })
    await flushPromises()
    await w.find('tr[data-hull="8002"]').trigger('dblclick')
    await flushPromises()
    expect(api.hull).toHaveBeenCalledWith('8002')
    expect(document.body.textContent).toContain('호선 8002')
    w.unmount()
    const ro = mount(HullList, { props: { menu: { ...menu, can_write: false } } })
    await flushPromises()
    expect(ro.find('[data-test=new-hull]').exists()).toBe(false)
    expect(ro.find('[data-test=readonly]').exists()).toBe(true)
  })
})

describe('HULL-T04 detail', () => {
  it('keeps the block sub tab after saving and notifies the list', async () => {
    const w = mount(HullDetailModal, { props: { hullNo: '8001', canWrite: true } })
    await flushPromises()
    await w.find('[data-subtab=blk]').trigger('click')
    await flushPromises()
    await w.find('input[name=block_cd]').setValue('999')
    await w.find('[data-test=blk-form]').trigger('submit')
    await flushPromises()
    expect(api.addBlock).toHaveBeenCalledWith('8001', { block_cd: '999', block_nm: '', block_type: null, weight_ton: null })
    expect(w.find('[data-subtab=blk]').classes()).toContain('act')
    expect(w.emitted('changed')).toHaveLength(1)
  })

  it('new hull shows only 기본정보 with PLAN default; read-only disables save', async () => {
    const w = mount(HullDetailModal, { props: { hullNo: 'new', canWrite: false } })
    await flushPromises()
    expect(w.find('.stabs').exists()).toBe(false)
    expect(w.find('select[name=hull_status]').element.value).toBe('PLAN')
    expect(w.find('[data-test=hull-save]').attributes('disabled')).toBeDefined()
  })
})

describe('SHELL-T04 hull popup navigation', () => {
  it('VIEWER-T01 3D tab: view-only users can open it, returning keeps unsaved edits, leaving unmounts the viewer', async () => {
    const stub = { ShipViewer: { template: '<div data-test="viewer" />' } }
    const w = mount(HullDetailModal, { props: { hullNo: '8002', canWrite: false }, global: { stubs: stub } })
    await flushPromises()
    await w.find('input[name=hull_nm]').setValue('수정중')
    const fetches = api.hull.mock.calls.length
    await w.find('[data-subtab="3d"]').trigger('click'); await flushPromises()
    expect(w.find('[data-test=viewer]').exists()).toBe(true)
    expect(w.find('.modal').classes()).toContain('xl')
    await w.find('[data-subtab=info]').trigger('click'); await flushPromises()
    expect(w.find('[data-test=viewer]').exists()).toBe(false)
    expect(w.find('.modal').classes()).toContain('large')
    expect(w.find('input[name=hull_nm]').element.value).toBe('수정중')
    expect(api.hull.mock.calls.length).toBe(fetches)
    await w.find('[data-subtab="3d"]').trigger('click')
    await w.find('[data-subtab=blk]').trigger('click'); await flushPromises() // a tab that was not loaded still loads
    expect(api.blocks).toHaveBeenCalled()
    w.unmount()
  })

  it('new hull has no 3D tab', async () => {
    const w = mount(HullDetailModal, { props: { hullNo: 'new', canWrite: true } })
    await flushPromises()
    expect(w.find('[data-subtab="3d"]').exists()).toBe(false)
    w.unmount()
  })

  it('summary 간트 보기 / 목록 보기 open target tab with this hull and close the popup', async () => {
    const navigate = vi.fn()
    const w = mount(HullDetailModal, { props: { hullNo: '8002', canWrite: false }, global: { provide: { navigate } } })
    await flushPromises()
    await w.find('[data-subtab=sum]').trigger('click'); await flushPromises()
    await w.find('[data-test=go-plan]').trigger('click')
    await w.find('[data-test=go-dwg-list]').trigger('click')
    expect(navigate.mock.calls).toEqual([['plan-gantt', '8002'], ['dwg-list', '8002']])
    expect(w.emitted('close')).toHaveLength(2)
  })
})
