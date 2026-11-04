// F10: VIEWER-T01/T04/T05 — lifecycle risks that a screenshot cannot catch. Rendering itself is verified in a real browser.
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ShipViewer from '../components/ShipViewer.vue'

const MANIFEST = { loaderUrl: 'v.loader.js', dataUrl: 'v.data', frameworkUrl: 'v.framework.js', codeUrl: 'v.wasm', companyName: 'c', productName: 'p', productVersion: '1' }
const fakeInstance = () => ({ SendMessage: vi.fn(), Quit: vi.fn(async () => {}) })
const manifestOk = () => ({ ok: true, headers: { get: () => 'application/json' }, json: async () => MANIFEST })
const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b }); return { promise, resolve, reject } }
const open = () => mount(ShipViewer, { attachTo: document.body })
const signalReady = async (w) => { w.find('canvas').element.dispatchEvent(new CustomEvent('shipviewer-ready')); await flushPromises() }

beforeEach(() => {
  HTMLCanvasElement.prototype.getContext = vi.fn(() => null)
  globalThis.fetch = vi.fn(async () => manifestOk())
  window.createUnityInstance = vi.fn(async () => fakeInstance())
})
afterEach(async () => {
  document.body.innerHTML = ''
  delete window.createUnityInstance
})

describe('F10 ship viewer', () => {
  it('shows the sample notice, blocks views until Unity signals ready, then sends messages', async () => {
    const inst = fakeInstance()
    window.createUnityInstance.mockResolvedValue(inst)
    const w = open(); await flushPromises()
    expect(w.find('canvas').element.id).not.toBe('') // the Unity runtime fails on a canvas without an id
    expect(w.find('[data-test=ship-notice]').text()).toBe('예시 모델 — 실제 호선 형상과 다름')
    expect(w.find('[data-test=ship-model]').text()).toBe('Demo Ship 01')
    expect(w.find('[data-view=front]').attributes('disabled')).toBeDefined()
    await signalReady(w)
    expect(w.find('[data-test=ship-loading]').exists()).toBe(false)
    await w.find('[data-view=top]').trigger('click')
    expect(inst.SendMessage).toHaveBeenCalledWith('ShipViewer', 'SetView', 'top')
    w.unmount(); await flushPromises()
    expect(inst.Quit).toHaveBeenCalledTimes(1)
  })

  it('VIEWER-T04 failure shows a message, keeps views blocked, and retry uses a fresh canvas', async () => {
    window.createUnityInstance.mockRejectedValueOnce('WebGL 미지원')
    const w = open(); await flushPromises()
    expect(w.find('[data-test=ship-error]').text()).toContain('WebGL 미지원')
    expect(w.find('[data-view=reset]').attributes('disabled')).toBeDefined()
    const first = w.find('canvas').element
    await w.find('[data-test=ship-retry]').trigger('click'); await flushPromises()
    expect(w.find('canvas').element).not.toBe(first)
    expect(window.createUnityInstance).toHaveBeenCalledTimes(2)
    await signalReady(w)
    expect(w.find('[data-test=ship-error]').exists()).toBe(false)
    w.unmount(); await flushPromises()
  })

  it('treats the SPA HTML fallback as a missing build', async () => {
    globalThis.fetch.mockResolvedValueOnce({ ok: true, headers: { get: () => 'text/html' } })
    const w = open(); await flushPromises()
    expect(w.find('[data-test=ship-error]').text()).toContain('빌드를 찾을 수 없습니다')
    expect(window.createUnityInstance).not.toHaveBeenCalled()
    w.unmount(); await flushPromises()
  })

  it('a loader script failure can be retried', async () => {
    delete window.createUnityInstance
    const w = open(); await flushPromises()
    document.querySelector('script[src$="v.loader.js"]').dispatchEvent(new Event('error'))
    await flushPromises()
    expect(w.find('[data-test=ship-error]').text()).toContain('로더를 불러오지 못했습니다')
    expect(document.querySelector('script[src$="v.loader.js"]')).toBe(null)
    w.unmount(); await flushPromises()
  })

  it('VIEWER-T05 closing during load quits the late instance and a reopen waits for it', async () => {
    const slow = deferred()
    const late = fakeInstance()
    window.createUnityInstance.mockReturnValueOnce(slow.promise)
    const first = open(); await flushPromises()
    first.unmount()
    const second = open(); await flushPromises()
    expect(window.createUnityInstance).toHaveBeenCalledTimes(1) // no overlap while the first is still loading
    slow.resolve(late); await flushPromises()
    expect(late.Quit).toHaveBeenCalledTimes(1)
    expect(window.createUnityInstance).toHaveBeenCalledTimes(2)
    await signalReady(second)
    expect(second.find('[data-view=front]').attributes('disabled')).toBeUndefined()
    second.unmount(); await flushPromises()
  })

  it('VIEWER-T05 repeated open/close leaves one quit per instance and no canvas behind', async () => {
    const made = []
    window.createUnityInstance.mockImplementation(async () => { const i = fakeInstance(); made.push(i); return i })
    for (let n = 0; n < 3; n++) {
      const w = open(); await flushPromises()
      await signalReady(w)
      expect(document.querySelectorAll('canvas')).toHaveLength(1)
      w.unmount(); await flushPromises()
    }
    expect(made).toHaveLength(3)
    made.forEach((i) => expect(i.Quit).toHaveBeenCalledTimes(1))
    expect(document.querySelectorAll('canvas')).toHaveLength(0)
  })
})
