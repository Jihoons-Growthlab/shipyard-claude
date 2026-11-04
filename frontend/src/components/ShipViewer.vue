<script setup>
// F10: sample ship viewer. Rendering lives in the Unity build; this component owns loading, state and teardown.
// The canvas needs an id: the Unity runtime looks it up as '#' + canvas.id.
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import ProgressBar from './ProgressBar.vue'
import { startUnity } from './unityRuntime'

const READY_TIMEOUT_MS = 20000
const VIEWS = [['front', '정면'], ['side', '측면'], ['top', '상단'], ['reset', '초기화']]

const canvas = ref(null)
const attempt = ref(0) // a retry gets a fresh canvas: a failed run may leave its WebGL context behind
const phase = ref('loading') // loading | ready | error
const progress = ref(0)
const error = ref('')
const percent = computed(() => Math.round(progress.value * 100))
let run = null
let instance = null
let cleanup = () => {}

function fail(message) {
  error.value = String(message || '알 수 없는 오류').split('\n')[0] // Unity errors carry a full stack trace
  phase.value = 'error'
  instance = null
  cleanup()
}

async function start() {
  phase.value = 'loading'; progress.value = 0; error.value = ''
  const el = canvas.value
  const current = startUnity(el, { onProgress: (p) => { progress.value = p }, onError: (m) => { if (run === current) fail(m) } })
  run = current
  let timer = null
  const signalled = new Promise((resolve) => {
    el.addEventListener('shipviewer-ready', resolve, { once: true })
    cleanup = () => { clearTimeout(timer); el.removeEventListener('shipviewer-ready', resolve) }
  })
  try {
    const created = await current.ready
    if (!created || run !== current) return
    timer = setTimeout(() => { if (run === current) fail('3D 뷰어가 응답하지 않습니다.') }, READY_TIMEOUT_MS)
    await signalled
    if (run !== current) return
    cleanup()
    instance = created
    phase.value = 'ready'
  } catch (e) {
    if (run === current) fail(e?.message || String(e))
  }
}

async function retry() {
  const failed = run
  run = null
  failed?.stop()
  attempt.value++
  await nextTick()
  start()
}

function setView(view) {
  if (phase.value === 'ready') instance?.SendMessage('ShipViewer', 'SetView', view)
}

onMounted(start)
onBeforeUnmount(() => {
  const current = run
  run = null
  instance = null
  cleanup()
  current?.stop()
})
defineExpose({ phase })
</script>

<template>
  <div class="sv">
    <section class="stage" data-test="ship-stage">
      <canvas id="unity-canvas" :key="attempt" ref="canvas" tabindex="-1" aria-label="샘플 선박 3D 화면" data-test="ship-canvas" @contextmenu.prevent />
      <div v-if="phase === 'loading'" class="cover" data-test="ship-loading">
        <b>3D 뷰어 불러오는 중…</b>
        <ProgressBar class="load" :value="percent" />
      </div>
      <div v-else-if="phase === 'error'" class="cover" data-test="ship-error">
        <b>3D 뷰어를 불러오지 못했습니다.</b>
        <span class="msg">{{ error }}</span>
        <button class="btn pri" data-test="ship-retry" @click="retry">재시도</button>
      </div>
    </section>
    <aside class="info">
      <section class="card">
        <h3>샘플 호선 3D 뷰어</h3>
        <div class="name" data-test="ship-model">Demo Ship 01</div>
        <div class="warnbox flush" data-test="ship-notice">예시 모델 — 실제 호선 형상과 다름</div>
      </section>
      <section class="card">
        <h3>시점</h3>
        <div class="views">
          <button v-for="[k, n] in VIEWS" :key="k" class="btn" :data-view="k" :disabled="phase !== 'ready'" @click="setView(k)">{{ n }}</button>
        </div>
      </section>
      <section class="card">
        <h3>조작 안내</h3>
        <ul class="help">
          <li><b>왼쪽 드래그</b> 회전</li>
          <li><b>휠</b> 확대·축소</li>
          <li><b>오른쪽 드래그</b> 화면 이동</li>
        </ul>
      </section>
    </aside>
  </div>
</template>

<style scoped>
.sv { flex:1; min-height:0; display:grid; grid-template-columns:minmax(0,1fr) 260px; gap:12px; }
.stage { position:relative; min-height:0; overflow:hidden; border:1px solid var(--line); border-radius:8px; background:#dde4ee; }
.stage canvas { position:absolute; inset:0; display:block; width:100%; height:100%; outline:0; }
.cover { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:10px; padding:16px; background:#dde4ee; text-align:center; }
.load { width:min(320px,80%); }
.msg { color:var(--muted); font-size:12px; max-width:480px; overflow-wrap:anywhere; }
.info { overflow:auto; }
.info .card:last-child { margin-bottom:0; }
.name { font-size:15px; font-weight:700; margin-bottom:8px; }
.flush { margin:0; }
.views { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.help { list-style:none; margin:0; padding:0; font-size:12px; line-height:1.9; }
.help b { display:inline-block; min-width:92px; font-weight:600; }
@media (max-width:760px) {
  .sv { grid-template-columns:1fr; grid-template-rows:minmax(260px,1fr) auto; }
  .info { max-height:40vh; }
}
</style>
