<script setup>
// F03 DASH-01~11: server-aggregated dashboard (GET /api/dashboard/summary). Navigation via shell-provided `navigate`.
import { computed, inject, onMounted, ref } from 'vue'
import { api } from '../../api/client'
import { codeName, loadCodes } from '../../stores/codes'
import { session } from '../../stores/session'
import { toast } from '../../stores/toast'
import DrawingDetailModal from '../drawings/DrawingDetailModal.vue'

defineProps({ menu: { type: Object, required: true }, param: { type: String, default: null } })
const navigate = inject('navigate', () => {})
const d = ref(null)
const dwg = ref(null) // DASH-11 drawing popup
const SC = { PLAN: '#9ca3af', READY: '#3b82f6', WORK: '#10b981', DONE: '#6366f1', DELAY: '#ef4444' }
const DC = { ISSUED: '#10b981', APPROVED: '#3b82f6', REVIEW: '#f59e0b', DRAFT: '#9ca3af' }
const dwgWrite = computed(() => !!(session.menu || []).find((m) => m.token === 'dwg-list')?.can_write)

async function load() {
  try { await loadCodes(); d.value = await api.dashboard() } catch (e) { toast(e.message, 'e') }
}
onMounted(load)

function go(link) {
  if (link.screen === 'drawing') dwg.value = link.param
  else navigate(link.screen, link.param ?? null)
}

const donut = computed(() => {
  const items = d.value?.plan_status || []
  const tot = items.reduce((s, i) => s + i.count, 0)
  const C = 2 * Math.PI * 40
  let off = 0
  const segs = items.filter((i) => i.count).map((i) => {
    const len = (i.count / (tot || 1)) * C
    const seg = { status: i.status, dash: `${len} ${C - len}`, off: -off }
    off += len
    return seg
  })
  return { tot, segs }
})
const monMax = computed(() => Math.max(1, ...(d.value?.deliveries || []).map((m) => m.count)))
const KPIS = [['active_hulls', '진행 호선', ''], ['delay_plans', '지연 공정', 'bad'], ['waiting_plans', '도면 대기 공정', 'warn'], ['pending_drawings', '결재·배포 대기 도면', 'warn']]
</script>

<template>
  <section class="pad dash" v-if="d">
    <h2>대시보드 <small class="muted">기준일 {{ d.today }} · 호선/공정/도면 현황</small></h2>
    <div class="kpis">
      <div v-for="[k, l, c] in KPIS" :key="k" class="kpi" :class="d.kpi[k].value ? c : ''" :data-test="`kpi-${k}`" @click="go(d.kpi[k].link)">
        <div class="l">{{ l }}</div><div class="v">{{ d.kpi[k].value }}</div>
      </div>
    </div>
    <div class="cols3">
      <div class="box" data-test="hull-progress"><h3>호선별 진척률</h3>
        <div v-for="h in d.hull_progress" :key="h.hull_no" class="hb" @click="go(h.link)">
          <span class="lb" :title="h.hull_nm">{{ h.hull_no }} {{ h.hull_nm }}</span>
          <span class="t"><i :style="{ width: h.progress + '%' }" /></span><b>{{ h.progress }}%</b>
        </div>
      </div>
      <div class="box" data-test="plan-status"><h3>공정 상태 분포</h3>
        <div class="donut">
          <svg width="120" height="120" viewBox="0 0 120 120">
            <circle v-for="s in donut.segs" :key="s.status" r="40" cx="60" cy="60" fill="none" :stroke="SC[s.status]" stroke-width="22"
                    :stroke-dasharray="s.dash" :stroke-dashoffset="s.off" transform="rotate(-90 60 60)" />
            <text x="60" y="58" text-anchor="middle" font-size="20" font-weight="700">{{ donut.tot }}</text>
            <text x="60" y="74" text-anchor="middle" font-size="10">전체</text>
          </svg>
          <div class="lg"><div v-for="s in d.plan_status" :key="s.status"><i :style="{ background: SC[s.status] }" />{{ codeName('PLANSTAT', s.status) }} <b>{{ s.count }}</b></div></div>
        </div>
      </div>
      <div class="box" data-test="disciplines"><h3>분야별 도면 상태</h3>
        <div v-for="g in d.drawing_disciplines" :key="g.discipline" class="disc">
          <div>{{ g.name }} <span class="muted">({{ g.total }})</span></div>
          <div class="stk"><template v-for="(n, s) in g.counts" :key="s"><div v-if="n" :style="{ width: (n / g.total) * 100 + '%', background: DC[s] }" :title="`${codeName('DWGSTAT', s)} ${n}`" /></template></div>
        </div>
        <div class="lg row"><span v-for="(c, s) in DC" :key="s"><i :style="{ background: c }" />{{ codeName('DWGSTAT', s) }}</span></div>
      </div>
    </div>
    <div class="cols3">
      <div class="box" data-test="deliveries"><h3>월별 인도 예정</h3>
        <div class="mcols"><div v-for="m in d.deliveries" :key="m.month" class="c">
          <b>{{ m.count }}</b><i :style="{ height: (m.count / monMax) * 80 + 'px' }" />
          <span class="muted">{{ m.month.slice(2) }}</span><span class="sm">{{ m.hull_nos.join(',') }}</span>
        </div></div>
      </div>
      <div class="box" data-test="delay-list"><h3>지연 공정 <span class="bdg bad">{{ d.delay_list.count }}</span></h3>
        <ul v-if="d.delay_list.items.length" class="lst"><li v-for="p in d.delay_list.items" :key="p.plan_id" @click="go(p.link)">
          <span>{{ p.hull_no }} {{ p.label }}</span><span class="m">{{ p.progress_rate }}% · 계획종료 {{ p.plan_end_dt }}</span></li></ul>
        <div v-else class="empty">지연 공정이 없습니다.</div>
      </div>
      <div class="box" data-test="waiting-list"><h3>도면 대기 공정 <span class="bdg warn">{{ d.waiting_list.count }}</span></h3>
        <ul v-if="d.waiting_list.items.length" class="lst"><li v-for="p in d.waiting_list.items" :key="p.plan_id" @click="go(p.link)">
          <span>{{ p.hull_no }} {{ p.label }}</span><span class="m">착수 {{ p.plan_start_dt }} · {{ p.blockers.join(', ') }}</span></li></ul>
        <div v-else class="empty">대기 중인 공정이 없습니다.</div>
      </div>
    </div>
    <div class="box" data-test="impact-list"><h3>도면 개정 영향 공정 <span class="bdg info">{{ d.impact_list.count }}</span></h3>
      <ul v-if="d.impact_list.items.length" class="lst"><li v-for="x in d.impact_list.items" :key="`${x.drawing_id}-${x.plan_id}`" @click="go(x.link)">
        <span>{{ x.drawing_no }} Rev{{ x.rev_no }} → {{ x.plan_label }} [{{ codeName('PLANSTAT', x.plan_status) }}]</span>
        <span class="m">{{ x.change_desc || '' }} · 배포 {{ x.issue_dt }}</span></li></ul>
      <div v-else class="empty">최근 개정된 도면의 영향 공정이 없습니다.</div>
    </div>
    <DrawingDetailModal v-if="dwg" :drawing-id="dwg" :can-write="dwgWrite" @close="dwg = null" @changed="load" @saved="load" @deleted="dwg = null; load()" />
  </section>
</template>

<style scoped>
.kpis { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:12px; }
.kpi { border:1px solid var(--line); border-radius:8px; padding:12px; cursor:pointer; }
.kpi .v { font-size:24px; font-weight:700; } .kpi.bad .v { color:#dc2626; } .kpi.warn .v { color:#d97706; }
.cols3 { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:12px; }
.box { border:1px solid var(--line); border-radius:8px; padding:12px; min-width:0; } .box h3 { margin:0 0 8px; font-size:14px; }
.hb { display:grid; grid-template-columns:140px 1fr 40px; gap:6px; align-items:center; cursor:pointer; margin:4px 0; font-size:12px; }
.hb .lb { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.hb .t { background:#e5e7eb; height:8px; border-radius:4px; } .hb .t i { display:block; height:100%; background:#3b82f6; border-radius:4px; }
.donut { display:flex; gap:12px; align-items:center; } .lg i { display:inline-block; width:10px; height:10px; margin-right:4px; }
.lg.row { display:flex; gap:8px; font-size:11px; flex-wrap:wrap; }
.disc { margin:8px 0; font-size:12px; } .stk { display:flex; height:10px; background:#f3f4f6; }
.mcols { display:flex; gap:10px; align-items:flex-end; } .mcols .c { display:flex; flex-direction:column; align-items:center; font-size:12px; }
.mcols i { width:22px; background:#6366f1; } .sm { font-size:10px; }
.lst { list-style:none; padding:0; margin:0; } .lst li { display:flex; justify-content:space-between; gap:8px; padding:5px 0; border-bottom:1px solid var(--line); cursor:pointer; font-size:12px; }
.lst .m { color:var(--muted); } .empty { color:var(--muted); font-size:12px; padding:8px 0; }
.bdg { font-size:11px; padding:1px 6px; border-radius:8px; background:#e5e7eb; } .bdg.bad { background:#fee2e2; } .bdg.warn { background:#fef3c7; } .bdg.info { background:#dbeafe; }
</style>
