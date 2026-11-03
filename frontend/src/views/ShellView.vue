<script setup>
// F02 shell: header, permission menu, MDI tabs with session restore.
import { computed, onMounted, provide, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import AppHeader from '../components/AppHeader.vue'
import MenuTree from '../components/MenuTree.vue'
import TabBar from '../components/TabBar.vue'
import ScreenPlaceholder from '../screens/ScreenPlaceholder.vue'
import { SCREEN_COMPONENTS } from '../screens/registry'
import { session } from '../stores/session'
import { createTabs } from '../stores/tabs'
import { toast } from '../stores/toast'

const router = useRouter()
const ready = ref(false)
const tabs = createTabs({ onError: (m) => toast(m, 'e') })

const screens = computed(() => Object.fromEntries(session.menu.filter((m) => m.token).map((m) => [m.token, m])))
const activeTab = computed(() => tabs.state.tabs.find((t) => t.key === tabs.state.active) || null)

function openMenu(m, param = null) {
  const r = tabs.open(m.token, m.title, param)
  if (r.opened) api.menuAccess(m.menu_id).catch((e) => { if (e.status === 403) { tabs.close(r.key); toast(e.message, 'e') } })
}

// F03 DASH-T05: screens navigate to another permitted screen (+ optional param, e.g. hull no).
// navRequest lets a reused tab (same screen+param) re-apply its hull context the user may have changed in place.
const navRequest = ref({ token: null, param: null, seq: 0 })
provide('navRequest', navRequest)
provide('navigate', (token, param = null) => {
  const m = screens.value[token]
  if (m) { openMenu(m, param); navRequest.value = { token, param, seq: navRequest.value.seq + 1 } }
  else toast('해당 화면에 대한 권한이 없습니다.', 'e')
})

onMounted(async () => {
  try { await session.load() } catch (e) { if (e.status !== 401) toast(e.message || '초기화에 실패했습니다.', 'e'); return } // 401 -> client redirects to login
  const titles = Object.fromEntries(Object.values(screens.value).map((m) => [m.token, m.title]))
  if (!tabs.restore(titles)) {
    const first = screens.value.dashboard || Object.values(screens.value)[0]
    if (first) openMenu(first)
  }
  ready.value = true
})

async function logout() {
  await session.logout()
  tabs.reset()
  router.replace('/login')
}
</script>

<template>
  <div v-if="ready && session.user" class="shell">
    <AppHeader :user="session.user" @logout="logout" />
    <div class="body">
      <MenuTree :items="session.menu" :active-token="activeTab?.token" @open="openMenu" />
      <main class="main">
        <TabBar :tabs="tabs.state.tabs" :active="tabs.state.active"
                @activate="tabs.activate" @close="tabs.close" @close-others="tabs.closeOthers" />
        <div class="panes">
          <template v-for="t in tabs.state.tabs" :key="t.key">
            <component :is="SCREEN_COMPONENTS[t.token] || ScreenPlaceholder" v-show="t.key === tabs.state.active" :menu="screens[t.token]" :param="t.param" />
          </template>
          <p v-if="!tabs.state.tabs.length" class="muted pad">왼쪽 메뉴에서 화면을 선택하세요.</p>
        </div>
      </main>
    </div>
  </div>
</template>
