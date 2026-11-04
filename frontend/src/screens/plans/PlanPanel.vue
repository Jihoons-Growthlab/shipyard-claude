<script setup>
// PLAN-02~04: add/edit, delete, predecessors, drawing links. Server validates and recomputes statuses.
import { computed, reactive, ref, watch } from 'vue'
import { api } from '../../api/client'
import { codeName } from '../../stores/codes'
import { toast } from '../../stores/toast'

const props = defineProps({
  plan: { type: Object, default: null },        // null => new
  hullNo: { type: String, required: true },
  defaultBlockId: { type: Number, default: null },
  today: { type: String, required: true },
  allPlans: { type: Array, required: true },    // whole hull, for predecessor options
  blocks: { type: Array, required: true },
  procs: { type: Array, required: true },
  users: { type: Array, required: true },
  canWrite: Boolean,
})
const emit = defineEmits(['saved', 'deleted', 'close', 'open-drawing'])
const isNew = computed(() => !props.plan)
const f = reactive({})
const dw = ref(null)
const link = reactive({ drawing_id: '', required: true })

const addDays = (iso, n) => new Date(Date.parse(iso + 'T00:00:00Z') + n * 864e5).toISOString().slice(0, 10)
function reset() {
  const p = props.plan
  Object.assign(f, p
    ? { block_id: p.block_id, proc_cd: p.proc_cd, plan_start_dt: p.plan_start_dt, plan_end_dt: p.plan_end_dt,
        manager_emp_no: p.manager_emp_no || '', remark: p.remark || '', pred_plan_ids: [...p.pred_plan_ids] }
    : { block_id: props.defaultBlockId, proc_cd: 'CUT', plan_start_dt: props.today, plan_end_dt: addDays(props.today, 13),
        manager_emp_no: '', remark: '', pred_plan_ids: [] })
}
async function loadDrawings() {
  dw.value = isNew.value ? null : await api.planDrawings(props.plan.plan_id).catch((e) => { toast(e.message, 'e'); return null })
}
watch(() => props.plan, () => { reset(); loadDrawings() }, { immediate: true })

const predOptions = computed(() => props.allPlans.filter((x) => x.plan_id !== props.plan?.plan_id))

async function save() {
  const body = { ...f, manager_emp_no: f.manager_emp_no || null, remark: f.remark || null }
  const send = (extra = {}) => (isNew.value ? api.createPlan(props.hullNo, { ...body, ...extra }) : api.updatePlan(props.plan.plan_id, { ...body, ...extra }))
  try {
    let saved
    try {
      saved = await send()
    } catch (e) {
      if (e.code !== 'PRED_LATE_CONFIRM_REQUIRED') throw e
      if (!confirm(e.message)) return        // PLAN-T04: cancel => nothing changes
      saved = await send({ confirm_late_preds: true })
    }
    toast('저장되었습니다.', 's')
    emit('saved', saved.plan_id)
  } catch (e) { toast(e.message, 'e') }
}
async function remove() {
  if (!confirm('공정을 삭제합니다. (실적·선후행·도면 연계 함께 삭제)')) return
  try { await api.deletePlan(props.plan.plan_id); toast('삭제되었습니다.', 's'); emit('deleted') } catch (e) { toast(e.message, 'e') }
}
async function addLink() {
  if (!link.drawing_id) return toast('도면을 선택하세요.', 'e')
  try {
    dw.value = await api.linkDrawing(props.plan.plan_id, Number(link.drawing_id), link.required)
    link.drawing_id = ''; link.required = true
    toast('도면이 연계되었습니다.', 's'); emit('saved', props.plan.plan_id)
  } catch (e) { toast(e.message, 'e') }
}
async function unlink(d) {
  try {
    await api.unlinkDrawing(props.plan.plan_id, d.drawing_id)
    toast('연계가 해제되었습니다.', 's'); emit('saved', props.plan.plan_id)
  } catch (e) { toast(e.message, 'e') }
}
defineExpose({ loadDrawings })
</script>

<template>
  <div class="pp" data-test="plan-panel">
    <div class="pp-h">
      <b>{{ isNew ? '공정 추가' : plan.label }}</b>
      <span v-if="!isNew" :class="['bdg', 's-' + plan.plan_status.toLowerCase()]">{{ codeName('PLANSTAT', plan.plan_status) }}</span>
      <span v-if="!isNew" class="muted">진척 {{ plan.progress_rate }}% · 실제 {{ plan.actual_start_dt || '-' }} ~ {{ plan.actual_end_dt || '-' }}</span>
    </div>
    <div class="pp-body">
      <form class="grid g6" data-test="plan-form" @submit.prevent="save">
        <label class="span2">블록<select v-model="f.block_id" name="block_id"><option :value="null">호선 전체(블록 없음)</option><option v-for="b in blocks" :key="b.block_id" :value="b.block_id">{{ b.block_cd }} {{ b.block_nm }}</option></select></label>
        <label class="w2">공정<select v-model="f.proc_cd" name="proc_cd"><option v-for="p in procs" :key="p.proc_cd" :value="p.proc_cd">{{ p.proc_nm }}</option></select></label>
        <label>계획 시작<input v-model="f.plan_start_dt" name="plan_start_dt" type="date" /></label>
        <label>계획 종료<input v-model="f.plan_end_dt" name="plan_end_dt" type="date" /></label>
        <label class="w2">담당자<select v-model="f.manager_emp_no" name="manager_emp_no"><option value="">미지정</option><option v-for="u in users" :key="u.emp_no" :value="u.emp_no">{{ u.display_name }} ({{ u.emp_no }})</option></select></label>
        <label class="span3">선행 공정 (Ctrl 다중선택)<select v-model="f.pred_plan_ids" name="preds" multiple size="3"><option v-for="x in predOptions" :key="x.plan_id" :value="x.plan_id">{{ x.label }}</option></select></label>
        <label class="span3">비고<textarea v-model="f.remark" name="remark" /></label>
        <div class="span6 bar">
          <button class="btn pri" data-test="plan-save" :disabled="!canWrite">저장</button>
          <button v-if="!isNew" class="btn dng" type="button" data-test="plan-delete" :disabled="!canWrite" @click="remove">삭제</button>
          <button class="btn" type="button" data-test="plan-close" @click="emit('close')">닫기</button>
        </div>
      </form>
      <div class="pp-r">
        <p v-if="isNew" class="muted">저장한 뒤 이 공정에 도면을 연계할 수 있습니다.</p>
        <template v-else-if="dw">
          <div v-if="dw.blockers.length" class="warnbox" data-test="gate-warn">
            📐 도면 대기: 필수 도면 <b>{{ dw.blockers.map((d) => `${d.drawing_no}(${codeName('DWGSTAT', d.dwg_status)})`).join(', ') }}</b> 미배포 → 착수 불가
          </div>
          <h4>연계 도면 <span class="muted">(필수 도면은 배포 전 착수 불가)</span></h4>
          <div class="tw r3"><table class="tbl">
            <thead><tr><th>도면번호</th><th>상태</th><th>필수</th><th></th></tr></thead>
            <tbody>
              <tr v-for="d in dw.links" :key="d.drawing_id" :data-link="d.drawing_no" :title="`${d.drawing_nm} · 필요일 ${d.need_dt || '-'}`">
                <td><a class="lnk" href="#" data-test="open-drawing" @click.prevent="emit('open-drawing', d.drawing_id)">{{ d.drawing_no }}</a></td>
                <td><span :class="['bdg', 'd-' + d.dwg_status.toLowerCase()]">{{ codeName('DWGSTAT', d.dwg_status) }}</span><span v-if="!d.has_issued" class="bdg b-warn"> 미배포</span></td>
                <td>{{ d.required ? '필수' : '참고' }}</td>
                <td><button class="btn sm dng" :disabled="!canWrite" data-test="unlink" @click="unlink(d)">해제</button></td>
              </tr>
              <tr v-if="!dw.links.length"><td colspan="4" class="muted">연계된 도면이 없습니다.</td></tr>
            </tbody>
          </table></div>
          <form class="bar" data-test="link-form" @submit.prevent="addLink">
            <select v-model="link.drawing_id" name="drawing_id"><option value="">도면 선택</option><option v-for="d in dw.available" :key="d.drawing_id" :value="d.drawing_id">{{ d.drawing_no }} {{ d.drawing_nm }}</option></select>
            <label><input v-model="link.required" type="checkbox" name="required" /> 필수</label>
            <button class="btn" data-test="link-add" :disabled="!canWrite">+ 연계</button>
          </form>
        </template>
      </div>
    </div>
  </div>
</template>
