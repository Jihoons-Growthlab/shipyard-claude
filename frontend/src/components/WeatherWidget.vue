<script setup>
// F02 WEATHER-01~03: region select (browser-local), refresh on change + every 10 min, LIVE vs SAMPLE badge.
// WEATHER-T03: a response that arrives after logout (unmount) or after a newer region request is discarded.
import { onMounted, onUnmounted, ref } from 'vue'
import { api } from '../api/client'

const REGIONS = ['울산', '거제', '목포']
const REFRESH_MS = 10 * 60 * 1000
const KEY = 'swp_region'
const props = defineProps({ storage: { type: Object, default: null } })
const store = props.storage || {
  get: () => { try { return localStorage.getItem(KEY) } catch { return null } },
  set: (v) => { try { localStorage.setItem(KEY, v) } catch { /* ignore */ } },
}

const saved = store.get()
const region = ref(REGIONS.includes(saved) ? saved : '울산')
const wx = ref(null) // { region, source, tempC, ... } | { failed: true }
let seq = 0
let alive = true
let timer = null

async function load() {
  const my = ++seq
  const r = region.value
  let next
  try { next = await api.weather(r) } catch (e) { next = { region: r, failed: true, error: e.message } }
  if (!alive || my !== seq || region.value !== r) return
  wx.value = next
}

function onRegion() { store.set(region.value); wx.value = null; load() }

const icon = (c = '') => (c.includes('맑') ? '☀️' : c.includes('구름') ? '⛅' : c.includes('흐') ? '☁️' : c.includes('눈') ? '❄️' : c.includes('비') ? '🌧️' : '🌤️')

defineExpose({ wx })
onMounted(() => { load(); timer = setInterval(load, REFRESH_MS) })
onUnmounted(() => { alive = false; clearInterval(timer) })
</script>

<template>
  <div class="wx" data-test="weather">
    <select v-model="region" title="지역 선택" data-test="region" @change="onRegion">
      <option v-for="r in REGIONS" :key="r" :value="r">{{ r }}</option>
    </select>
    <span v-if="!wx">날씨 조회 중…</span>
    <span v-else-if="wx.failed" data-test="wx-failed" :title="wx.error">날씨 조회 실패</span>
    <template v-else>
      <span>{{ icon(wx.condition) }}</span><b data-test="wx-temp">{{ wx.tempC ?? '-' }}℃</b><span>{{ wx.condition }}</span>
      <span>{{ wx.humidity != null ? `습도 ${wx.humidity}%` : '' }}{{ wx.windMs != null ? ` · 바람 ${wx.windMs}m/s` : '' }}</span>
      <span v-if="wx.source === 'LIVE'" class="src live" data-test="wx-badge" :title="`MCP 실시간${wx.obsDt ? ' · 관측 ' + wx.obsDt : ''}`">LIVE</span>
      <span v-else class="src" data-test="wx-badge" :title="`실시간 조회 실패(${wx.error || ''}) — 화면 확인용 샘플값`">샘플</span>
    </template>
  </div>
</template>
