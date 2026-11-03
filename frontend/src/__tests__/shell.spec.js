// F02 SHELL-T01~T05 (client side; server 403 for SHELL-T01 is in backend/tests/test_rbac_shell.py)
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import MenuTree from '../components/MenuTree.vue'
import BaseModal from '../components/BaseModal.vue'
import ScreenPlaceholder from '../screens/ScreenPlaceholder.vue'
import { createTabs, MAX_TABS } from '../stores/tabs'

const memStorage = () => { const m = new Map(); return { get: (k) => m.get(k) ?? null, set: (k, v) => m.set(k, v), remove: (k) => m.delete(k) } }

// /api/me/menu response for DWG group (no M22 progress, no M90/M91)
const DWG_MENU = [
  { menu_id: 'M00', parent_id: null, title: '대시보드', token: 'dashboard', can_write: false },
  { menu_id: 'M10', parent_id: null, title: '호선관리', token: null, can_write: false },
  { menu_id: 'M11', parent_id: 'M10', title: '호선 목록', token: 'hull-list', can_write: false },
  { menu_id: 'M20', parent_id: null, title: '공정관리', token: null, can_write: false },
  { menu_id: 'M21', parent_id: 'M20', title: '공정 계획', token: 'plan-gantt', can_write: false },
  { menu_id: 'M30', parent_id: null, title: '도면관리', token: null, can_write: true },
  { menu_id: 'M31', parent_id: 'M30', title: '도면 목록', token: 'dwg-list', can_write: true },
  { menu_id: 'M33', parent_id: 'M30', title: '결재함', token: 'dwg-approval', can_write: true },
]

describe('SHELL-T01 permission menu', () => {
  it('renders only server-permitted menus and emits open for leaves', async () => {
    const w = mount(MenuTree, { props: { items: DWG_MENU } })
    const ids = w.findAll('[data-menu]').map((a) => a.attributes('data-menu'))
    expect(ids).toEqual(['M00', 'M11', 'M21', 'M31', 'M33'])
    expect(w.text()).not.toContain('공정 실적')
    expect(w.text()).not.toContain('회원관리')
    await w.find('[data-menu="M31"]').trigger('click')
    expect(w.emitted('open')[0][0].token).toBe('dwg-list')
  })
  it('SHELL-03 toggles group open/closed', async () => {
    const w = mount(MenuTree, { props: { items: DWG_MENU } })
    const sub = () => w.find('[data-menu="M11"]').element.closest('ul')
    expect(sub().style.display).toBe('')
    await w.find('[data-group="M10"]').trigger('click')
    expect(sub().style.display).toBe('none')
    await w.find('[data-group="M10"]').trigger('click')
    expect(sub().style.display).toBe('')
  })
  it('SHELL-07 shows 조회 전용 for View-only screens', () => {
    expect(mount(ScreenPlaceholder, { props: { menu: DWG_MENU[2] } }).find('[data-test="readonly"]').exists()).toBe(true)
    expect(mount(ScreenPlaceholder, { props: { menu: DWG_MENU[6] } }).find('[data-test="readonly"]').exists()).toBe(false)
  })
})

describe('MDI tabs', () => {
  let storage, onError, tabs
  beforeEach(() => { storage = memStorage(); onError = vi.fn(); tabs = createTabs({ storage, onError }) })

  it('SHELL-T02 same screen+param reuses one tab', () => {
    tabs.open('dwg-list', '도면 목록')
    tabs.open('hull-list', '호선 목록')
    const r = tabs.open('dwg-list', '도면 목록')
    expect(r.reused).toBe(true)
    expect(tabs.state.tabs).toHaveLength(2)
    expect(tabs.state.active).toBe('dwg-list:')
    tabs.open('dwg-list', '도면 목록', '42')
    expect(tabs.state.tabs).toHaveLength(3)
  })

  it('SHELL-T03 13th tab is refused with error and existing tabs untouched', () => {
    for (let i = 0; i < MAX_TABS; i++) tabs.open('hull-list', `T${i}`, String(i))
    const before = JSON.stringify(tabs.state)
    const r = tabs.open('dwg-list', '도면 목록')
    expect(r.error).toBe('MAX_TABS')
    expect(onError).toHaveBeenCalledOnce()
    expect(JSON.stringify(tabs.state)).toBe(before)
    expect(tabs.state.tabs).toHaveLength(12)
    // reusing an existing tab at the limit still works
    expect(tabs.open('hull-list', 'T3', '3').reused).toBe(true)
  })

  it('SHELL-04 close and close others', () => {
    tabs.open('dashboard', '대시보드'); tabs.open('hull-list', '호선 목록'); tabs.open('dwg-list', '도면 목록')
    tabs.close('dwg-list:')
    expect(tabs.state.active).toBe('hull-list:')
    tabs.open('dwg-list', '도면 목록')
    tabs.closeOthers('hull-list:')
    expect(tabs.state.tabs.map((t) => t.key)).toEqual(['hull-list:'])
  })

  it('SHELL-T05 restore keeps only permitted tabs', () => {
    tabs.open('dashboard', '대시보드'); tabs.open('progress', '공정 실적'); tabs.open('user-mgmt', '회원관리'); tabs.open('dwg-list', '도면 목록')
    const again = createTabs({ storage })
    const n = again.restore({ dashboard: '대시보드', 'dwg-list': '도면 목록' }) // e.g. DWG user: no progress/user-mgmt
    expect(n).toBe(2)
    expect(again.state.tabs.map((t) => t.token)).toEqual(['dashboard', 'dwg-list'])
    expect(again.state.active).toBe('dwg-list:')
  })

  it('SHELL-T05 nothing permitted -> 0 (caller opens dashboard); corrupt storage is ignored', () => {
    tabs.open('user-mgmt', '회원관리')
    expect(createTabs({ storage }).restore({ dashboard: '대시보드' })).toBe(0)
    storage.set('swp_tabs', '{broken')
    expect(createTabs({ storage }).restore({ dashboard: '대시보드' })).toBe(0)
  })
})

describe('SHELL-T04 modal', () => {
  it('closes with Esc and the close button; inner clicks do not close', async () => {
    const w = mount(BaseModal, { props: { open: true, title: '호선 상세' }, slots: { default: '<button class="pick">선택</button>' }, attachTo: document.body })
    await w.find('.pick').trigger('click')
    expect(w.emitted('close')).toBeUndefined()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(w.emitted('close')).toHaveLength(1)
    await w.find('[data-test="modal-close"]').trigger('click')
    expect(w.emitted('close')).toHaveLength(2)
    await w.setProps({ open: false }); await nextTick()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(w.emitted('close')).toHaveLength(2)
    w.unmount()
  })
})
