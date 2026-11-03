<script setup>
// F05 PLAN-01: gantt with hull/block/zoom filters, dependency arrows, today line, drawing-wait marker, detail panel.
import { computed, inject, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../../api/client'
import { codeList, codeName, loadCodes } from '../../stores/codes'
import { toast } from '../../stores/toast'
import PlanPanel from './PlanPanel.vue'
import { LABEL_W, ROW_H, ZOOMS, initialScroll, layout } from './ganttLayout'

const props = defineProps({ menu: { type: Object, required: true }, param: { type: String, default: null } })
const s = reactive({ hull: '', block: '', ppd: 4, sel: null }) // sel: plan_id | 'new' | null
const hulls = ref([])
const blocks = ref([])
const data = ref(null)
const procs = ref([])
const users = ref([])
const scroller = ref(null)
let scrollLeft = null // null => compute from TODAY (40%)

const allPlans = computed(() => data.value?.plans || [])
const rows = computed(() => allPlans.value.filter((p) => !s.block || p.block_id === Number(s.block)))
const lay = computed(() => (data.value ? layout(rows.value, data.value.today, s.ppd) : null))
const idx = computed(() => Object.fromEntries(rows.value.map((p, i) => [p.plan_id, i])))
const byId = computed(() => Object.fromEntries(allPlans.value.map((p) => [p.plan_id, p])))
const arrows = computed(() => {
  if (!lay.value) return []
  return data.value.deps.filter((d) => d.plan_id in idx.value && d.pred_plan_id in idx.value).map((d) => {
    const a = byId.value[d.pred_plan_id], b = byId.value[d.plan_id]
    const x1 = lay.value.ux(a.plan_end_dt, 1), y1 = idx.value[a.plan_id] * ROW_H + 14
    const x2 = lay.value.ux(b.plan_start_dt), y2 = idx.value[b.plan_id] * ROW_H + 14
    return `M${x1.toFixed(2)} ${y1} H${(x1 + 4).toFixed(2)} V${y2} H${x2.toFixed(2)}`
  })
})
const selPlan = computed(() => (typeof s.sel === 'number' ? byId.value[s.sel] || null : null))

async function applyScroll() {
  await nextTick()
  const g = scroller.value
  if (!g || !g.clientWidth || !lay.value) return
  if (scrollLeft === null) scrollLeft = initialScroll(lay.value, g.clientWidth)
  g.scrollLeft = scrollLeft
}
const remember = () => { if (scroller.value) scrollLeft = scroller.value.scrollLeft }

async function load() {
  if (!s.hull) return
  try {
    const [d, b] = await Promise.all([api.plans(s.hull), api.blocks(s.hull).catch(() => [])])
    data.value = d; blocks.value = b
    if (typeof s.sel === 'number' && !byId.value[s.sel]) s.sel = null
    applyScroll()
  } catch (e) { toast(e.message, 'e') }
}

watch(() => s.hull, () => { s.block = ''; s.sel = null; scrollLeft = null; if (scroller.value) scroller.value.scrollTop = 0; load() })
watch(() => s.block, () => { if (scroller.value) scroller.value.scrollTop = 0; applyScroll() })
// Navigation into this (possibly reused) tab restores its hull context
const navRequest = inject('navRequest', ref({}))
watch(navRequest, (r) => { if (r.token === 'plan-gantt' && props.param && r.param === props.param && hulls.value.some((h) => h.hull_no === r.param)) s.hull = r.param })
watch(() => s.ppd, () => { scrollLeft = null; applyScroll() })

onMounted(async () => {
  try {
    await loadCodes()
    ;[hulls.value, procs.value, users.value] = await Promise.all([api.planHulls(), api.procs(), api.userOptions()])
    s.hull = (props.param && hulls.value.find((h) => h.hull_no === props.param)) ? props.param : (hulls.value.find((h) => h.plan_count) || hulls.value[0] || {}).hull_no || ''
  } catch (e) { toast(e.message, 'e') }
})

async function onSaved(id) { remember(); s.sel = id; await load() }
async function onDeleted() { remember(); s.sel = null; await load() }
function pick(p) { remember(); s.sel = p.plan_id }
defineExpose({ s, scroller })
</script>

<template>
  <section class="screen plan">
    <div class="ph">
      <h2>{{ menu.title }}</h2>
      <span v-if="!menu.can_write" class="badge ro" data-test="readonly">조회 전용</span>
    </div>
    <div class="bar">
      <select v-model="s.hull" name="hull"><option v-for="h in hulls" :key="h.hull_no" :value="h.hull_no">{{ h.hull_no }} {{ h.hull_nm }}</option></select>
      <select v-model="s.block" name="block"><option value="">블록 전체</option><option v-for="b in blocks" :key="b.block_id" :value="String(b.block_id)">{{ b.block_cd }} {{ b.block_nm }}</option></select>
      <select v-model.number="s.ppd" name="zoom"><option v-for="z in ZOOMS" :key="z.v" :value="z.v">{{ z.label }}</option></select>
      <span data-test="hull-progress">호선 진척 {{ data?.hull_progress ?? '-' }}{{ data?.hull_progress != null ? '%' : '' }}</span>
      <button v-if="menu.can_write" class="btn pri right" data-test="plan-new" @click="remember(); s.sel = 'new'">+ 공정 추가</button>
    </div>
    <div class="glegend">
      <span v-for="c in codeList('PLANSTAT')" :key="c.code"><i :class="'c-' + c.code.toLowerCase()" />{{ c.name }}</span>
      <span>📐 도면 대기</span><span class="muted">— 선후행 연결선 / 빨간선 = 오늘({{ data?.today }})</span>
    </div>

    <div v-if="data && !rows.length" class="muted pad">표시할 공정이 없습니다.</div>
    <div v-else-if="lay" ref="scroller" class="g3" data-test="gantt" @scroll.passive="remember">
      <div class="g3in" :style="{ width: lay.width + 'px' }">
        <div class="g2row g2head">
          <div class="g2l" :style="{ width: LABEL_W + 'px' }">블록 / 공정</div>
          <div class="g2t"><div v-for="m in lay.months" :key="m.label" class="gm" :style="{ left: m.left + '%', width: m.width + '%' }">{{ m.label }}</div></div>
        </div>
        <div class="gbody">
          <div v-for="p in rows" :key="p.plan_id" :class="['g2row', { sel: s.sel === p.plan_id }]" :data-plan="p.plan_id" @click="pick(p)">
            <div class="g2l" :style="{ width: LABEL_W + 'px' }" :title="p.label"><span class="bc">{{ p.block_cd ?? '호선' }}</span> {{ p.proc_nm }}<span v-if="p.drawing_wait" data-test="dwg-wait"> 📐</span></div>
            <div class="g2t">
              <div :class="['gbar', 'c-' + p.plan_status.toLowerCase()]" :style="{ left: lay.bars[p.plan_id].left + '%', width: lay.bars[p.plan_id].width + '%' }"
                   :title="`${p.label}\n${p.plan_start_dt} ~ ${p.plan_end_dt}\n진척 ${p.progress_rate}% · ${codeName('PLANSTAT', p.plan_status)}${p.drawing_wait ? '\n도면 대기' : ''}`">
                <i :style="{ width: p.progress_rate + '%' }" />
              </div>
            </div>
          </div>
          <div class="g2ov" :style="{ left: LABEL_W + 'px' }">
            <div v-for="m in lay.months" :key="'v' + m.label" class="gvl" :style="{ left: m.left + '%' }" />
            <div class="gtoday" data-test="today" :style="{ left: lay.todayPct + '%' }"><span>오늘</span></div>
            <svg class="gsvg" :viewBox="`0 0 1000 ${rows.length * ROW_H}`" preserveAspectRatio="none" width="100%" :height="rows.length * ROW_H">
              <path v-for="(d, i) in arrows" :key="i" :d="d" vector-effect="non-scaling-stroke" fill="none" stroke="#64748b" stroke-width="1" opacity=".55" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <p v-if="!s.sel" class="muted">막대 또는 좌측 공정명을 클릭하면 상세/수정 패널이 열립니다.</p>
    <PlanPanel v-else-if="s.sel === 'new' || selPlan" :key="s.sel" :plan="selPlan" :hull-no="s.hull" :default-block-id="s.block ? Number(s.block) : null"
               :today="data?.today || ''" :all-plans="allPlans" :blocks="blocks" :procs="procs" :users="users" :can-write="menu.can_write"
               @saved="onSaved" @deleted="onDeleted" @close="s.sel = null" />
  </section>
</template>
