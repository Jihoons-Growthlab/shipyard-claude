import { reactive } from 'vue'
import { api, configureClient } from '../api/client'
import { safeSession } from './storage'

const TOKEN_KEY = 'swp_token'
export const TABS_KEY = 'swp_tabs'

export const session = reactive({
  token: safeSession.get(TOKEN_KEY),
  user: null,
  menu: [],
  onExpired: null,

  setToken(t) {
    this.token = t
    t ? safeSession.set(TOKEN_KEY, t) : safeSession.remove(TOKEN_KEY)
  },
  async load() {
    // AUTH-05: server re-checks approved status + open session on every call
    const [user, menu] = await Promise.all([api.me(), api.menu()])
    this.user = user
    this.menu = menu
  },
  clear() {
    this.setToken(null)
    this.user = null
    this.menu = []
    safeSession.remove(TABS_KEY)
  },
  async logout() {
    try { await api.logout() } catch { /* token may already be invalid */ }
    this.clear()
  },
})

configureClient({
  getToken: () => session.token,
  unauthorized: () => { session.clear(); session.onExpired?.() },
})
