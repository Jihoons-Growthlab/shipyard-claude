import { reactive } from 'vue'
import { safeSession } from './storage'
import { TABS_KEY } from './session'

export const MAX_TABS = 12
export const tabKey = (token, param) => `${token}:${param ?? ''}`

// SHELL-04/05: MDI tabs — reuse by screen+param, max 12, close / close others, session restore.
export function createTabs({ storage = safeSession, onError = () => {} } = {}) {
  const state = reactive({ tabs: [], active: null })

  const persist = () =>
    storage.set(TABS_KEY, JSON.stringify({
      tabs: state.tabs.map(({ token, param }) => ({ token, param })),
      active: state.active,
    }))

  function open(token, title, param = null) {
    const key = tabKey(token, param)
    if (state.tabs.some((t) => t.key === key)) {
      state.active = key
      persist()
      return { key, reused: true }
    }
    if (state.tabs.length >= MAX_TABS) {
      onError(`탭은 최대 ${MAX_TABS}개까지 열 수 있습니다. 사용하지 않는 탭을 닫아주세요.`)
      return { key: null, error: 'MAX_TABS' }
    }
    state.tabs.push({ key, token, title, param })
    state.active = key
    persist()
    return { key, opened: true }
  }

  function close(key) {
    const i = state.tabs.findIndex((t) => t.key === key)
    if (i < 0) return
    state.tabs.splice(i, 1)
    if (state.active === key) state.active = state.tabs[Math.min(i, state.tabs.length - 1)]?.key ?? null
    persist()
  }

  function closeOthers(key) {
    state.tabs = state.tabs.filter((t) => t.key === key)
    state.active = state.tabs[0]?.key ?? null
    persist()
  }

  function activate(key) {
    if (state.tabs.some((t) => t.key === key)) { state.active = key; persist() }
  }

  /** Restore only tabs whose screen is still permitted. `screens`: token -> title. Returns restored count. */
  function restore(screens) {
    let saved
    try { saved = JSON.parse(storage.get(TABS_KEY) || 'null') } catch { saved = null }
    const list = (saved?.tabs || []).filter((t) => t && Object.hasOwn(screens, t.token)).slice(0, MAX_TABS)
    state.tabs = list.map((t) => ({ key: tabKey(t.token, t.param), token: t.token, title: screens[t.token], param: t.param ?? null }))
    state.active = state.tabs.some((t) => t.key === saved?.active) ? saved.active : state.tabs[0]?.key ?? null
    persist()
    return state.tabs.length
  }

  function reset() { state.tabs = []; state.active = null }

  return { state, open, close, closeOthers, activate, restore, reset }
}
