// F02 WEATHER-T01~T03 (client): region request, LIVE vs SAMPLE badge, stale responses after region change/logout ignored
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

vi.mock('../api/client', () => ({ api: { weather: vi.fn() } }))
import { api } from '../api/client'
import WeatherWidget from '../components/WeatherWidget.vue'

const mem = (v = null) => { let x = v; return { get: () => x, set: (n) => { x = n } } }
const res = (region, source = 'SAMPLE', tempC = 17.6) => ({ region, source, tempC, condition: '맑음', humidity: 52, windMs: 3.2, obsDt: null, error: source === 'SAMPLE' ? '미설정' : null })
const deferred = () => { let resolve; const p = new Promise((r) => { resolve = r }); return { p, resolve } }

describe('F02 weather widget', () => {
  beforeEach(() => { vi.clearAllMocks(); vi.useFakeTimers() })
  afterEach(() => vi.useRealTimers())

  it('WEATHER-T01 defaults to 울산, requests selected region, persists it, refreshes every 10 min', async () => {
    api.weather.mockImplementation(async (r) => res(r))
    const store = mem()
    const w = mount(WeatherWidget, { props: { storage: store } }); await flushPromises()
    expect(api.weather).toHaveBeenLastCalledWith('울산')
    for (const r of ['거제', '목포']) {
      await w.find('[data-test=region]').setValue(r); await flushPromises()
      expect(api.weather).toHaveBeenLastCalledWith(r)
      expect(store.get()).toBe(r)
    }
    const n = api.weather.mock.calls.length
    vi.advanceTimersByTime(10 * 60 * 1000); await flushPromises()
    expect(api.weather).toHaveBeenCalledTimes(n + 1)
    w.unmount()
  })

  it('WEATHER-T02 SAMPLE / failure never shows LIVE; LIVE only when server says so', async () => {
    api.weather.mockResolvedValueOnce(res('울산'))
    let w = mount(WeatherWidget, { props: { storage: mem() } }); await flushPromises()
    expect(w.find('[data-test=wx-badge]').text()).toBe('샘플'); expect(w.text()).not.toContain('LIVE'); w.unmount()
    api.weather.mockRejectedValueOnce(new Error('down'))
    w = mount(WeatherWidget, { props: { storage: mem() } }); await flushPromises()
    expect(w.find('[data-test=wx-failed]').exists()).toBe(true); expect(w.text()).not.toContain('LIVE'); w.unmount()
    api.weather.mockResolvedValueOnce(res('울산', 'LIVE', 20.1))
    w = mount(WeatherWidget, { props: { storage: mem() } }); await flushPromises()
    expect(w.find('[data-test=wx-badge]').text()).toBe('LIVE'); expect(w.find('[data-test=wx-temp]').text()).toBe('20.1℃'); w.unmount()
  })

  it('WEATHER-T03 late response after region change or unmount (logout) is ignored', async () => {
    const slow = deferred(), fast = deferred()
    api.weather.mockReturnValueOnce(slow.p).mockReturnValueOnce(fast.p)
    const w = mount(WeatherWidget, { props: { storage: mem() } })
    await w.find('[data-test=region]').setValue('목포')
    fast.resolve(res('목포', 'SAMPLE', 16.2)); await flushPromises()
    slow.resolve(res('울산', 'LIVE', 99)); await flushPromises()
    expect(w.find('[data-test=wx-temp]').text()).toBe('16.2℃'); expect(w.text()).not.toContain('LIVE')

    const late = deferred()
    api.weather.mockReturnValueOnce(late.p)
    vi.advanceTimersByTime(10 * 60 * 1000)
    const vm = w.vm
    expect(vm.wx.tempC).toBe(16.2)
    w.unmount()
    late.resolve(res('목포', 'LIVE', 50)); await flushPromises()
    expect(api.weather).toHaveBeenCalledTimes(3)
    expect(vm.wx.tempC).toBe(16.2) // not overwritten by the late LIVE 50
  })
})
