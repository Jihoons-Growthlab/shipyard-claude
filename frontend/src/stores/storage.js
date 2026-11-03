// sessionStorage may throw (private mode); keep the app working without it.
export const safeSession = {
  get(k) { try { return sessionStorage.getItem(k) } catch { return null } },
  set(k, v) { try { sessionStorage.setItem(k, v) } catch { /* ignore */ } },
  remove(k) { try { sessionStorage.removeItem(k) } catch { /* ignore */ } },
}
