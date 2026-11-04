// F10 Unity Web lifecycle (contracts/unity-viewer.md). One instance at a time: a new start waits until the
// previous one has fully quit, because createUnityInstance cannot be cancelled while it is loading.
const BUILD_URL = '/unity/ship-viewer/Build/'
let loader = null
let previous = Promise.resolve()

async function fetchManifest() {
  const res = await fetch(`${BUILD_URL}build.json`, { cache: 'no-store' })
  const type = res.headers.get('content-type') || ''
  if (!res.ok || !type.includes('json')) throw new Error('3D 뷰어 빌드를 찾을 수 없습니다.') // SPA fallback answers with HTML
  return res.json()
}

function loadScript(src) {
  if (window.createUnityInstance) return Promise.resolve()
  loader ??= new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = src
    script.onload = () => (window.createUnityInstance ? resolve() : reject(new Error('Unity 로더가 올바르지 않습니다.')))
    script.onerror = () => reject(new Error('Unity 로더를 불러오지 못했습니다.'))
    document.body.appendChild(script)
  }).catch((e) => {
    document.querySelector(`script[src="${src}"]`)?.remove()
    loader = null // allow retry
    throw e
  })
  return loader
}

async function quit(instance, canvas) {
  try { await instance.Quit() } catch { /* already gone */ }
  canvas.getContext('webgl2')?.getExtension('WEBGL_lose_context')?.loseContext()
}

export function startUnity(canvas, { onProgress, onError }) {
  let stopped = false
  let instance = null
  let finish
  const finished = new Promise((resolve) => { finish = resolve })
  const wait = previous
  previous = finished

  const ready = (async () => {
    try {
      await wait
      if (stopped) return null
      const m = await fetchManifest()
      if (stopped) return null
      await loadScript(BUILD_URL + m.loaderUrl)
      if (stopped) return null
      const created = await window.createUnityInstance(canvas, {
        dataUrl: BUILD_URL + m.dataUrl,
        frameworkUrl: BUILD_URL + m.frameworkUrl,
        codeUrl: BUILD_URL + m.codeUrl,
        companyName: m.companyName,
        productName: m.productName,
        productVersion: m.productVersion,
        devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2),
        showBanner: (message, type) => { if (type === 'error' && !stopped) onError(message) }, // replaces Unity's default banner
      }, (p) => { if (!stopped) onProgress(p) })
      if (stopped) { await quit(created, canvas); return null } // closed during loading: discard the late result
      instance = created
      return created
    } finally {
      if (!instance) finish()
    }
  })()

  return {
    ready,
    async stop() {
      if (stopped) return finished
      stopped = true
      if (instance) { await quit(instance, canvas); finish() }
      return finished
    },
  }
}
