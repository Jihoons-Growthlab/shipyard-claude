import { reactive } from 'vue'
import { api } from '../api/client'

// Common codes (TB_SYS_Code), loaded once per session.
export const codes = reactive({ groups: {}, loaded: null })
export function loadCodes() {
  codes.loaded ||= api.codes().then((g) => { codes.groups = g }).catch((e) => { codes.loaded = null; throw e })
  return codes.loaded
}
export const codeList = (g) => codes.groups[g] || []
export const codeName = (g, c) => codeList(g).find((x) => x.code === c)?.name || c || ''
