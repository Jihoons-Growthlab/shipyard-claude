<script setup>
// F06 PROG-01~03: progress targets, daily cumulative input (upsert by work date), history delete. Server validates/recomputes.
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../../api/client'
import ProgressBar from '../../components/ProgressBar.vue'
import { codeName, loadCodes } from '../../stores/codes'
import { session } from '../../stores/session'
import { toast } from '../../stores/toast'

const props = defineProps({ menu: { type: Object, required: true } })
const s = reactive({ hull: '', showDone: false, sel: null })
const hulls = ref([])
const users = ref([])
const data = ref(null)
const detail = ref(null) // { plan, history }
const f = reactive({})
const busy = ref(false)

const plans = computed(() => data.value?.plans || [])
const today = computed(() => data.value?.today || '')

function resetForm() {
  Object.assign(f, { work_dt: today.value, progress_rate: detail.value?.plan.progress_rate ?? 0, man_hour: '', worker_cnt: '',
    worker_emp_no: session.user?.emp_no || '', remark: '' })
}

async function loadList() {
  if (!s.hull) return
  try {
    data.value = await api.progressTargets(s.hull, s.showDone)
    if (s.sel && !plans.value.some((p) => p.plan_id === s.sel)) { s.sel = null; detail.value = null }
  } catch (e) { toast(e.message, 'e') }
}

async function loadDetail() {
  if (!s.sel) { detail.value = null; return }
  try { detail.value = await api.planProgress(s.sel); resetForm() } catch (e) { toast(e.message, 'e') }
}

watch(() => s.hull, () => { s.sel = null; detail.value = null; loadList() })
watch(() => s.showDone, loadList)
watch(() => s.sel, loadDetail)

onMounted(async () => {
  try {
    await loadCodes()
    const [h, u] = await Promise.all([api.progressHulls(), api.userOptions()])
    hulls.value = h.hulls; users.value = u
    s.hull = h.default_hull_no || ''
  } catch (e) { toast(e.message, 'e') }
})

const num = (v) => (v === '' || v === null || v === undefined ? null : Number(v))

async function save() {
  busy.value = true
  try {
    const rate = num(f.progress_rate)
    detail.value = await api.saveProgress(s.sel, f.work_dt, { progress_rate: rate, man_hour: num(f.man_hour),
      worker_cnt: num(f.worker_cnt), worker_emp_no: f.worker_emp_no || null, remark: f.remark || null })
    toast(rate >= 100 ? '실적 저장 — 공정이 완료 처리되었습니다.' : '실적이 저장되었습니다.', 's')
    resetForm()
    await loadList()
  } catch (e) { toast(e.message, 'e') } finally { busy.value = false }
}

async function remove(row) {
  if (!confirm('실적을 삭제합니다.')) return
  try {
    detail.value = await api.deleteProgress(row.progress_id)
    toast('실적이 삭제되었습니다.', 's')
    await loadList()
  } catch (e) { toast(e.message, 'e') }
}
defineExpose({ s, f, save, remove })
</script>

<template>
  <section class="screen progress">
    <div class="ph">
      <h2>공정 실적 입력</h2>
      <span class="d">착수 가능/진행/지연 공정의 일별 진척률·공수를 입력하면 공정 진척과 상태가 갱신됩니다.</span>
      <span v-if="!menu.can_write" class="badge ro" data-test="readonly">조회 전용</span>
    </div>
    <div class="bar">
      <select v-model="s.hull" name="hull"><option v-for="h in hulls" :key="h.hull_no" :value="h.hull_no">{{ h.hull_no }} {{ h.hull_nm }}</option></select>
      <label><input v-model="s.showDone" type="checkbox" name="showDone"> 완료 공정 포함</label>
    </div>
    <table class="tbl" data-test="targets">
      <thead><tr><th>공정</th><th>계획기간</th><th>실제착수</th><th>진척</th><th>상태</th><th>담당</th></tr></thead>
      <tbody>
        <tr v-for="p in plans" :key="p.plan_id" :class="{ sel: s.sel === p.plan_id }" :data-plan="p.plan_id" @click="s.sel = p.plan_id">
          <td>{{ p.label }}</td><td>{{ p.plan_start_dt }} ~ {{ p.plan_end_dt }}</td><td>{{ p.actual_start_dt || '-' }}</td>
          <td style="min-width:130px"><ProgressBar :value="p.progress_rate" /></td>
          <td><span :class="['bdg', 's-' + p.plan_status.toLowerCase()]">{{ codeName('PLANSTAT', p.plan_status) }}</span></td>
          <td>{{ p.manager_nm || '' }}</td>
        </tr>
        <tr v-if="!plans.length"><td colspan="6">대상 공정이 없습니다.</td></tr>
      </tbody>
    </table>

    <div v-if="detail" class="panel" data-test="detail">
      <h3>{{ detail.plan.label }} <span :class="['bdg', 's-' + detail.plan.plan_status.toLowerCase()]">{{ codeName('PLANSTAT', detail.plan.plan_status) }}</span></h3>
      <form v-if="menu.can_write" class="grid g6" @submit.prevent="save">
        <label>작업일<input v-model="f.work_dt" type="date" name="work_dt" :max="today"></label>
        <label>누적 진척률(%)<input v-model="f.progress_rate" type="number" name="progress_rate" min="0" max="100" step="1"></label>
        <label>투입 공수(MH)<input v-model="f.man_hour" type="number" name="man_hour" step="0.5"></label>
        <label>투입 인원<input v-model="f.worker_cnt" type="number" name="worker_cnt"></label>
        <label>작업자<select v-model="f.worker_emp_no" name="worker_emp_no"><option value="">-</option><option v-for="u in users" :key="u.emp_no" :value="u.emp_no">{{ u.display_name }} ({{ u.emp_no }})</option></select></label>
        <div><button class="btn pri" type="submit" :disabled="busy">실적 저장</button></div>
        <label>비고<input v-model="f.remark" name="remark"></label>
      </form>
      <h3 class="h3t">실적 이력</h3>
      <table class="tbl" data-test="history">
        <thead><tr><th>작업일</th><th>누적 진척률</th><th>공수</th><th>인원</th><th>작업자</th><th>비고</th><th /></tr></thead>
        <tbody>
          <tr v-for="x in detail.history" :key="x.progress_id">
            <td>{{ x.work_dt }}</td><td>{{ x.progress_rate }}%</td><td class="num">{{ x.man_hour ?? '' }}</td>
            <td class="num">{{ x.worker_cnt ?? '' }}</td><td>{{ x.worker_nm || '' }}</td><td>{{ x.remark || '' }}</td>
            <td><button v-if="menu.can_write" class="btn sm dng" type="button" @click="remove(x)">삭제</button></td>
          </tr>
          <tr v-if="!detail.history.length"><td colspan="7">실적 이력이 없습니다.</td></tr>
        </tbody>
      </table>
    </div>
    <div v-else class="note">위 목록에서 공정을 선택하세요.</div>
  </section>
</template>
