<script setup>
// F04 HULL-02~07: detail popup with sub tabs (info / milestones / blocks / summary). Server enforces all rules.
import { computed, inject, reactive, ref, watch } from 'vue'
import { api } from '../../api/client'
import BaseModal from '../../components/BaseModal.vue'
import ProgressBar from '../../components/ProgressBar.vue'
import ShipViewer from '../../components/ShipViewer.vue'
import { codeList, codeName } from '../../stores/codes'
import { toast } from '../../stores/toast'

const props = defineProps({ hullNo: { type: String, required: true }, canWrite: Boolean })
const emit = defineEmits(['close', 'saved', 'deleted', 'changed'])
// SHELL-T04: mockup goPlan/goDwgList — open the target tab with this hull, then close the popup (mockup openTab closes MODAL)
const navigate = inject('navigate', () => {})
function goto(screen) { navigate(screen, props.hullNo); emit('close') }

const isNew = computed(() => props.hullNo === 'new')
const tab = ref('info')
let loaded = null // data tab currently in the form; the 3D tab holds no data, so returning from it must not refetch over unsaved edits
const form = reactive({})
const ms = ref([])
const blocks = ref([])
const summary = ref(null)
const blk = reactive({ block_cd: '', block_nm: '', block_type: '', weight_ton: '' })
const title = computed(() => (isNew.value ? '호선 등록' : `호선 ${props.hullNo}`))
const FIELDS = ['hull_no', 'hull_nm', 'ship_type', 'hull_status', 'owner_nm', 'class_society', 'length_m', 'breadth_m',
  'depth_m', 'dead_weight', 'dock_no', 'contract_dt', 'delivery_dt', 'remark', 'use_yn']
const NUMS = ['length_m', 'breadth_m', 'depth_m', 'dead_weight']

const fail = (e) => toast(e.message, 'e')
const num = (v) => (v === '' || v === null || v === undefined ? null : Number(v))

async function loadInfo() {
  if (isNew.value) {
    FIELDS.forEach((k) => { form[k] = '' })
    Object.assign(form, { hull_status: 'PLAN', use_yn: true })
    return
  }
  const h = await api.hull(props.hullNo)
  FIELDS.forEach((k) => { form[k] = h[k] ?? '' })
  form.use_yn = h.use_yn
}
async function loadTab() {
  loaded = tab.value
  try {
    if (tab.value === 'info') await loadInfo()
    else if (tab.value === 'ms') ms.value = await api.milestones(props.hullNo)
    else if (tab.value === 'blk') blocks.value = await api.blocks(props.hullNo)
    else if (tab.value === 'sum') summary.value = await api.hullSummary(props.hullNo)
  } catch (e) { fail(e) }
}
// HULL-T04: keep the current sub tab when the same popup reloads; new -> created hull switches to its detail
watch(() => props.hullNo, (n, o) => { if (o === 'new' || !o) tab.value = 'info'; loadTab() }, { immediate: true })
watch(tab, (t) => { if (t !== '3d' && t !== loaded) loadTab() })

function payload() {
  const b = {}
  FIELDS.forEach((k) => { b[k] = NUMS.includes(k) ? num(form[k]) : form[k] === '' ? null : form[k] })
  b.use_yn = !!form.use_yn
  return b
}
async function save() {
  try {
    if (isNew.value) {
      const h = await api.createHull(payload())
      toast('호선이 등록되었습니다.', 's')
      emit('saved', h.hull_no)
    } else {
      const { hull_no, ...rest } = payload()
      await api.updateHull(props.hullNo, rest)
      toast('저장되었습니다.', 's')
      await loadInfo()
      emit('changed')
    }
  } catch (e) { fail(e) }
}
async function remove() {
  if (!confirm(`호선 ${props.hullNo} 및 하위 데이터(블록·공정·도면)를 모두 삭제합니다. 계속할까요?`)) return
  try { await api.deleteHull(props.hullNo); toast('삭제되었습니다.', 's'); emit('deleted') } catch (e) { fail(e) }
}
async function saveMs() {
  try {
    ms.value = await api.saveMilestones(props.hullNo, ms.value.map((m) => ({ milestone_cd: m.milestone_cd, plan_dt: m.plan_dt || null, actual_dt: m.actual_dt || null })))
    toast('주요일정이 저장되었습니다.', 's')
  } catch (e) { fail(e) }
}
async function addBlock() {
  try {
    await api.addBlock(props.hullNo, { block_cd: blk.block_cd, block_nm: blk.block_nm, block_type: blk.block_type || null, weight_ton: num(blk.weight_ton) })
    Object.assign(blk, { block_cd: '', block_nm: '', block_type: '', weight_ton: '' })
    blocks.value = await api.blocks(props.hullNo)
    toast('블록이 추가되었습니다.', 's'); emit('changed')
  } catch (e) { fail(e) }
}
async function delBlock(b) {
  if (!confirm('블록과 해당 블록의 공정을 삭제합니다. (도면의 블록 연결은 해제)')) return
  try { await api.deleteBlock(b.block_id); blocks.value = await api.blocks(props.hullNo); toast('삭제되었습니다.', 's'); emit('changed') } catch (e) { fail(e) }
}
</script>

<template>
  <BaseModal open :large="tab !== '3d'" :xl="tab === '3d'" :title="title" @close="emit('close')">
    <p class="mnote">{{ isNew ? '신규 호선을 등록합니다.' : codeName('HULLSTAT', form.hull_status) }}</p>
    <div v-if="!isNew" class="stabs">
      <a v-for="[k, n] in [['info', '기본정보'], ['ms', '주요일정'], ['blk', '블록 구성'], ['sum', '연계 현황'], ['3d', '3D 보기']]" :key="k"
         :class="{ act: tab === k }" :data-subtab="k" @click="tab = k">{{ n }}</a>
    </div>

    <form v-if="tab === 'info'" class="card grid g4" data-test="hull-form" @submit.prevent="save">
      <label>호선번호 *<input v-model="form.hull_no" name="hull_no" :readonly="!isNew" /></label>
      <label class="span2">호선명<input v-model="form.hull_nm" name="hull_nm" /></label>
      <label>선종<select v-model="form.ship_type" name="ship_type"><option value="">선택</option><option v-for="c in codeList('SHIPTYPE')" :key="c.code" :value="c.code">{{ c.name }}</option></select></label>
      <label>상태<select v-model="form.hull_status" name="hull_status"><option v-for="c in codeList('HULLSTAT')" :key="c.code" :value="c.code">{{ c.name }}</option></select></label>
      <label class="span2">선주<input v-model="form.owner_nm" name="owner_nm" /></label>
      <label>선급<input v-model="form.class_society" name="class_society" /></label>
      <label>전장(m)<input v-model="form.length_m" name="length_m" type="number" step="0.01" /></label>
      <label>선폭(m)<input v-model="form.breadth_m" name="breadth_m" type="number" step="0.01" /></label>
      <label>선심(m)<input v-model="form.depth_m" name="depth_m" type="number" step="0.01" /></label>
      <label>재화중량(DWT)<input v-model="form.dead_weight" name="dead_weight" type="number" /></label>
      <label>도크/건조장소<input v-model="form.dock_no" name="dock_no" /></label>
      <label>계약일<input v-model="form.contract_dt" name="contract_dt" type="date" /></label>
      <label>인도 예정일<input v-model="form.delivery_dt" name="delivery_dt" type="date" /></label>
      <label>사용여부<span class="ck"><input v-model="form.use_yn" name="use_yn" type="checkbox" />사용</span></label>
      <label class="span4">비고<input v-model="form.remark" name="remark" /></label>
      <div class="span4 bar">
        <button class="btn pri" data-test="hull-save" :disabled="!canWrite">저장</button>
        <button v-if="!isNew" class="btn dng" type="button" data-test="hull-delete" :disabled="!canWrite" @click="remove">삭제</button>
        <span class="note">삭제 시 블록·공정·도면이 함께 삭제됩니다(FK CASCADE).</span>
      </div>
    </form>

    <div v-else-if="tab === 'ms'" class="card">
      <table class="tbl">
        <thead><tr><th>일정</th><th>계획일</th><th>실적일</th><th>차이(일)</th></tr></thead>
        <tbody>
          <tr v-for="m in ms" :key="m.milestone_cd">
            <td>{{ m.name }}</td><td><input v-model="m.plan_dt" type="date" /></td>
            <td><input v-model="m.actual_dt" type="date" /></td><td class="num">{{ m.diff_days ?? '-' }}</td>
          </tr>
        </tbody>
      </table>
      <div class="bar sub-acts"><button class="btn pri" data-test="ms-save" :disabled="!canWrite" @click="saveMs">일정 저장</button></div>
    </div>

    <div v-else-if="tab === 'blk'" class="card">
      <table class="tbl">
        <thead><tr><th>블록코드</th><th>블록명</th><th>유형</th><th>중량(ton)</th><th>진척</th><th>공정</th><th>도면</th><th></th></tr></thead>
        <tbody>
          <tr v-for="b in blocks" :key="b.block_id" :data-block="b.block_cd">
            <td><b>{{ b.block_cd }}</b></td><td>{{ b.block_nm }}</td><td>{{ codeName('BLOCKTYPE', b.block_type) }}</td>
            <td class="num">{{ b.weight_ton ?? '' }}</td><td style="min-width:110px"><template v-if="b.progress === null">-</template><ProgressBar v-else :value="b.progress" /></td>
            <td class="num">{{ b.plan_count }}</td><td class="num">{{ b.drawing_count }}</td>
            <td><button class="btn sm dng" :disabled="!canWrite" data-test="blk-delete" @click="delBlock(b)">삭제</button></td>
          </tr>
          <tr v-if="!blocks.length"><td colspan="8" class="muted">블록이 없습니다.</td></tr>
        </tbody>
      </table>
      <form class="bar sub-acts" data-test="blk-form" @submit.prevent="addBlock">
        <input v-model="blk.block_cd" name="block_cd" placeholder="블록코드 *" />
        <input v-model="blk.block_nm" name="block_nm" placeholder="블록명" />
        <select v-model="blk.block_type" name="block_type"><option value="">유형 선택</option><option v-for="c in codeList('BLOCKTYPE')" :key="c.code" :value="c.code">{{ c.name }}</option></select>
        <input v-model="blk.weight_ton" name="weight_ton" type="number" placeholder="중량(ton)" />
        <button class="btn pri" data-test="blk-add" :disabled="!canWrite">+ 블록 추가</button>
      </form>
    </div>

    <div v-else-if="tab === 'sum' && summary" class="cols2">
      <div class="card-p">
        <h4>공정 <button class="btn sm" data-test="go-plan" @click="goto('plan-gantt')">간트 보기</button></h4>
        <template v-if="summary.plan_count">
          <p>전체 진척 {{ summary.progress }}%</p>
          <ul><li v-for="(v, k) in summary.plan_status" :key="k">{{ codeName('PLANSTAT', k) }}: {{ v }}</li></ul>
        </template>
        <p v-else class="muted">공정 계획이 없습니다.</p>
      </div>
      <div class="card-p">
        <h4>도면 <button class="btn sm" data-test="go-dwg-list" @click="goto('dwg-list')">목록 보기</button></h4>
        <ul v-if="summary.drawing_count"><li v-for="(v, k) in summary.drawing_status" :key="k">{{ codeName('DWGSTAT', k) }}: {{ v }}</li></ul>
        <p v-else class="muted">도면이 없습니다.</p>
      </div>
    </div>

    <ShipViewer v-else-if="tab === '3d'" />
  </BaseModal>
</template>

<style scoped>
.mnote { margin:0 0 10px; color:var(--muted); font-size:12px; }
.sub-acts { margin-top:12px; }
.grid .bar { margin:2px 0 0; }
.grid .bar .note { margin:0; }
</style>
