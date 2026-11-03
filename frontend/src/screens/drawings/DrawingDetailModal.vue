<script setup>
// F07 DWG-02~05: drawing form, PDF viewer (uploaded file vs labelled sample), revisions, approval request/issue, plan links.
// Server enforces RBAC, DRAFT-only file changes, revision state transitions and BR-02 gate recompute.
import { computed, inject, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../../api/client'
import BaseModal from '../../components/BaseModal.vue'
import { codeList, codeName } from '../../stores/codes'
import { session } from '../../stores/session'
import { toast } from '../../stores/toast'
import { pdfError } from './pdf'

const props = defineProps({ drawingId: { type: [Number, String], required: true }, canWrite: Boolean })
// SHELL-T04: mockup goPlan from linked plans — linked plans always share the drawing's hull
const navigate = inject('navigate', () => {})
const emit = defineEmits(['close', 'saved', 'deleted', 'changed'])


const isNew = computed(() => props.drawingId === 'new')
const d = ref(null)
const hulls = ref([])
const blocks = ref([])
const users = ref([])
const form = reactive({ drawing_no: '', drawing_nm: '', hull_no: '', block_id: '', discipline: 'HULL', designer_emp_no: '' })
const newPdf = ref(null)
const revForm = reactive({ change_desc: '', file: null })
const apr = reactive({ reviewer: 'lee.dwg', approver: 'admin' })
const link = reactive({ plan_id: '', required: true })
const vrev = ref(null)
const viewer = reactive({ url: '', sample: false, error: '' })

const latest = computed(() => d.value?.revisions[0] || null)
const shown = computed(() => d.value?.revisions.find((r) => r.rev_no === vrev.value) || latest.value)
const title = computed(() => (isNew.value ? '도면 등록' : d.value ? `도면 ${d.value.drawing_no}` : '도면 상세'))

const fail = (e) => toast(e.message, 'e')
function revoke() { if (viewer.url) URL.revokeObjectURL(viewer.url); viewer.url = '' }

async function loadPdf() {
  revoke(); viewer.sample = false; viewer.error = ''
  const r = shown.value
  if (!r) return
  if (!r.has_file) { viewer.sample = true; return } // DWG-T05: never shown as a real file
  try { viewer.url = URL.createObjectURL(await api.pdfBlob(d.value.drawing_id, r.rev_no)) } catch (e) { viewer.error = e.message }
}

async function loadBlocks(hullNo) { blocks.value = hullNo ? await api.blocks(hullNo).catch(() => []) : [] }

async function load() {
  if (isNew.value) return
  try {
    d.value = await api.drawing(props.drawingId)
    Object.assign(form, { drawing_no: d.value.drawing_no, drawing_nm: d.value.drawing_nm, hull_no: d.value.hull_no,
      block_id: d.value.block_id ?? '', discipline: d.value.discipline, designer_emp_no: d.value.designer_emp_no || '' })
    if (vrev.value === null || !d.value.revisions.some((r) => r.rev_no === vrev.value)) vrev.value = latest.value?.rev_no ?? null
    await loadBlocks(d.value.hull_no)
    await loadPdf()
  } catch (e) { fail(e) }
}

onMounted(async () => {
  try {
    ;[hulls.value, users.value] = await Promise.all([api.hulls().catch(() => []), api.userOptions().catch(() => [])])
    if (isNew.value) {
      Object.assign(form, { hull_no: hulls.value[0]?.hull_no || '', designer_emp_no: session.user?.emp_no || '' })
      await loadBlocks(form.hull_no)
    }
  } catch (e) { fail(e) }
  await load()
})
onBeforeUnmount(revoke)
watch(vrev, (v, old) => { if (old !== null && d.value) loadPdf() })

async function onHullChange() { form.block_id = ''; await loadBlocks(form.hull_no) } // DWG-02: reset block options

async function save() {
  const body = { drawing_nm: form.drawing_nm, block_id: form.block_id === '' ? null : Number(form.block_id),
    discipline: form.discipline, designer_emp_no: form.designer_emp_no || null }
  try {
    if (isNew.value) {
      if (newPdf.value) { const er = pdfError(newPdf.value); if (er) return toast(er, 'e') }
      const created = await api.createDrawing({ ...body, drawing_no: form.drawing_no, hull_no: form.hull_no })
      let msg = ''
      if (newPdf.value) {
        try { await api.uploadPdf(created.drawing_id, 0, newPdf.value); msg = ' PDF 첨부됨.' } catch (e) { msg = ` (PDF 저장 실패: ${e.message})` }
      }
      toast('도면이 등록되었습니다. (Rev0 작성중)' + msg, 's')
      emit('saved', created.drawing_id)
    } else {
      d.value = await api.updateDrawing(d.value.drawing_id, body)
      toast('저장되었습니다.', 's'); emit('changed')
    }
  } catch (e) { fail(e) }
}

async function remove() {
  if (!confirm('도면과 리비전·결재·공정 연계를 삭제합니다.')) return
  try { await api.deleteDrawing(d.value.drawing_id); toast('삭제되었습니다.', 's'); emit('deleted') } catch (e) { fail(e) }
}

async function upload(ev) {
  const file = ev.target.files?.[0]; ev.target.value = ''
  if (!file) return
  const er = pdfError(file); if (er) return toast(er, 'e')
  try { await api.uploadPdf(d.value.drawing_id, shown.value.rev_no, file); toast(`Rev${shown.value.rev_no}에 PDF를 업로드했습니다.`, 's'); await load(); await loadPdf() } catch (e) { fail(e) }
}
async function removeFile() {
  if (!confirm('업로드한 PDF를 삭제합니다.')) return
  try { await api.deletePdf(d.value.drawing_id, shown.value.rev_no); toast('파일을 삭제했습니다.', 's'); await load(); await loadPdf() } catch (e) { fail(e) }
}
function openNew() { if (viewer.url) window.open(viewer.url, '_blank'); else toast('표시 중인 PDF가 없습니다.', 'e') }

async function after(p, msg) {
  try { d.value = await p; toast(msg, 's'); vrev.value = latest.value.rev_no; await loadPdf(); emit('changed') } catch (e) { fail(e) }
}
async function createRev() {
  if (revForm.file) { const er = pdfError(revForm.file); if (er) return toast(er, 'e') }
  await after(api.newRevision(d.value.drawing_id, revForm.change_desc), `Rev${latest.value.rev_no + 1} 작성중으로 생성되었습니다.`)
  if (revForm.file && latest.value?.rev_status === 'DRAFT') {
    try { await api.uploadPdf(d.value.drawing_id, latest.value.rev_no, revForm.file); await load(); await loadPdf() } catch (e) { fail(e) }
  }
  Object.assign(revForm, { change_desc: '', file: null })
}
const requestApproval = () => after(api.requestApproval(d.value.drawing_id, latest.value.rev_no, apr.reviewer, apr.approver), '결재가 요청되었습니다.')
const issue = () => after(api.issueRevision(d.value.drawing_id, latest.value.rev_no), '도면이 배포되었습니다. 연계 공정 상태가 갱신됩니다.')

async function addLink() {
  if (!link.plan_id) return toast('공정을 선택하세요.', 'e')
  try { Object.assign(d.value, await api.linkPlan(d.value.drawing_id, Number(link.plan_id), link.required)); link.plan_id = ''; toast('공정이 연계되었습니다.', 's'); emit('changed') } catch (e) { fail(e) }
}
async function removeLink(p) {
  try { Object.assign(d.value, await api.unlinkPlan(d.value.drawing_id, p.plan_id)); toast('연계가 해제되었습니다.', 's'); emit('changed') } catch (e) { fail(e) }
}
const apResult = (r) => ({ WAIT: '대기', APPROVE: '승인', REJECT: '반려' }[r] || r)
defineExpose({ form, d, viewer, vrev, save, upload, createRev, requestApproval, issue, addLink })
</script>

<template>
  <BaseModal open xl :title="title" @close="emit('close')">
    <div :class="['dwgx', { solo: isNew }]">
      <!-- DWG-03 viewer -->
      <section v-if="!isNew" class="card vcard" data-test="viewer">
        <div class="bar">
          <select v-model.number="vrev" name="vrev"><option v-for="r in d?.revisions || []" :key="r.rev_no" :value="r.rev_no">Rev{{ r.rev_no }} ({{ codeName('DWGSTAT', r.rev_status) }})</option></select>
          <span v-if="shown?.has_file" class="badge" data-test="uploaded">업로드 파일</span>
          <span v-else class="badge warn" data-test="sample">샘플 PDF (미업로드)</span>
          <span class="sp" />
          <template v-if="canWrite && shown?.rev_status === 'DRAFT'">
            <label class="btn sm upl">PDF {{ shown.has_file ? '교체' : '업로드' }}<input type="file" accept=".pdf,application/pdf" hidden data-test="upload" @change="upload"></label>
            <button v-if="shown.has_file" class="btn sm dng" @click="removeFile">파일 삭제</button>
          </template>
          <button class="btn sm" @click="openNew">새 창 ↗</button>
        </div>
        <div class="pdfbox">
          <iframe v-if="viewer.url" :src="viewer.url + '#view=FitH'" title="PDF" />
          <div v-else-if="viewer.sample" class="pdfmsg" data-test="sample-box">
            <b>샘플 PDF (미업로드)</b><br>{{ d?.drawing_no }} · Rev{{ shown?.rev_no }} · {{ codeName('DWGSTAT', shown?.rev_status) }}<br>
            <small>이 리비전에는 업로드된 도면 파일이 없습니다.</small>
          </div>
          <div v-else class="pdfmsg">{{ viewer.error || '불러오는 중…' }}</div>
        </div>
      </section>

      <div class="side">
        <!-- DWG-02 form -->
        <section class="card">
          <h3>도면 정보</h3>
          <form class="grid4" @submit.prevent="save">
            <label class="span2">도면번호<input v-model="form.drawing_no" name="drawing_no" :readonly="!isNew"></label>
            <label class="span2">도면명<input v-model="form.drawing_nm" name="drawing_nm"></label>
            <label>호선<select v-model="form.hull_no" name="hull_no" :disabled="!isNew" @change="onHullChange"><option v-for="h in hulls" :key="h.hull_no" :value="h.hull_no">{{ h.hull_no }}</option></select></label>
            <label>블록<select v-model="form.block_id" name="block_id"><option value="">블록 없음</option><option v-for="b in blocks" :key="b.block_id" :value="b.block_id">{{ b.block_cd }} {{ b.block_nm }}</option></select></label>
            <label>분야<select v-model="form.discipline" name="discipline"><option v-for="c in codeList('DWGDISC')" :key="c.code" :value="c.code">{{ c.name }}</option></select></label>
            <label>설계자<select v-model="form.designer_emp_no" name="designer_emp_no"><option value="">-</option><option v-for="u in users" :key="u.emp_no" :value="u.emp_no">{{ u.display_name }}</option></select></label>
            <label v-if="isNew" class="span4">도면 파일 (PDF, 선택)<input type="file" name="pdf" accept=".pdf,application/pdf" @change="newPdf = $event.target.files[0] || null"></label>
            <div v-if="canWrite" class="span4 acts">
              <button class="btn pri" type="submit" data-test="save">{{ isNew ? '등록' : '저장' }}</button>
              <button v-if="!isNew" class="btn dng" type="button" data-test="delete" @click="remove">삭제</button>
            </div>
          </form>
        </section>

        <template v-if="d">
          <!-- DWG-04 revision actions -->
          <section v-if="canWrite && latest" class="card" data-test="rev-action">
            <h3>리비전 작업</h3>
            <form v-if="['ISSUED', 'OBSOLETE'].includes(latest.rev_status)" class="grid4" @submit.prevent="createRev">
              <label class="span4">신규 Rev{{ latest.rev_no + 1 }} 개정 사유<input v-model="revForm.change_desc" name="change_desc"></label>
              <label class="span4">도면 파일 (PDF, 선택)<input type="file" accept=".pdf,application/pdf" @change="revForm.file = $event.target.files[0] || null"></label>
              <div class="span4 acts"><button class="btn pri" type="submit">신규 Rev 작성</button></div>
            </form>
            <form v-else-if="latest.rev_status === 'DRAFT'" class="grid4" @submit.prevent="requestApproval">
              <div class="span4 note">Rev{{ latest.rev_no }} 작성중입니다. 검토자/승인자를 지정해 결재를 요청하세요.</div>
              <label class="span2">1단계 검토자<select v-model="apr.reviewer" name="reviewer"><option v-for="u in users" :key="u.emp_no" :value="u.emp_no">{{ u.display_name }}</option></select></label>
              <label class="span2">2단계 승인자<select v-model="apr.approver" name="approver"><option v-for="u in users" :key="u.emp_no" :value="u.emp_no">{{ u.display_name }}</option></select></label>
              <div class="span4 acts"><button class="btn pri" type="submit">결재 요청</button></div>
            </form>
            <div v-else-if="latest.rev_status === 'REVIEW'" class="note">Rev{{ latest.rev_no }} 결재 진행중입니다. 결재자는 [결재함]에서 처리합니다.</div>
            <div v-else-if="latest.rev_status === 'APPROVED'" class="acts">
              <span class="note">Rev{{ latest.rev_no }} 승인 완료 — 배포하면 연계 공정의 도면 게이트가 열립니다.</span>
              <button class="btn pri" data-test="issue" @click="issue">Rev{{ latest.rev_no }} 배포</button>
            </div>
          </section>

          <section class="card">
            <h3>리비전 이력 <span class="bdg">{{ d.revisions.length }}</span></h3>
            <div class="tw">
              <table class="tbl fit" data-test="revisions">
                <colgroup><col style="width:56px"><col style="width:64px"><col><col style="width:100px"><col style="width:62px"></colgroup>
                <thead><tr><th>Rev</th><th>상태</th><th>변경 사유 / 파일</th><th>작성 · 배포</th><th /></tr></thead>
                <tbody>
                  <tr v-for="r in d.revisions" :key="r.rev_no" :class="{ sel: r.rev_no === shown?.rev_no }">
                    <td>Rev{{ r.rev_no }}</td><td>{{ codeName('DWGSTAT', r.rev_status) }}</td>
                    <td class="wrap">{{ r.change_desc }}<div class="sub">{{ r.has_file ? r.file_nm : (r.file_nm ? `${r.file_nm} (미업로드)` : '파일 없음') }}</div></td>
                    <td>{{ r.author_nm || '-' }}<div class="sub">{{ r.issue_dt || '미배포' }}</div></td>
                    <td class="num"><button class="btn sm" @click="vrev = r.rev_no">보기</button></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section class="card">
            <h3>결재 이력</h3>
            <div class="tw">
              <table class="tbl" data-test="approvals">
                <thead><tr><th>Rev</th><th>단계</th><th>결재자</th><th>결과</th></tr></thead>
                <tbody>
                  <tr v-for="a in d.approvals" :key="a.approval_id" :title="`${a.comment || ''} ${a.act_dt || ''}`">
                    <td>Rev{{ a.rev_no }}</td><td>{{ a.step_no === 1 ? '검토' : '승인' }}</td><td>{{ a.approver_nm || '' }}</td><td>{{ apResult(a.result) }}</td>
                  </tr>
                  <tr v-if="!d.approvals.length"><td colspan="4" class="empty">결재 이력이 없습니다.</td></tr>
                </tbody>
              </table>
            </div>
          </section>

          <section class="card">
            <h3>연계 공정 <span class="bdg">{{ d.plans.length }}</span></h3>
            <div v-if="d.impacts.length" class="warnbox" data-test="impact">
              ⚠ 최근 개정(Rev{{ d.impacts[0].rev_no }}, {{ d.impacts[0].issue_dt }})으로 이미 착수·완료된 공정 <b>{{ d.impacts.length }}건</b>이 영향을 받습니다:
              {{ d.impacts.map((i) => i.plan_label).join(', ') }}
            </div>
            <div class="tw">
              <table class="tbl" data-test="links">
                <thead><tr><th>공정</th><th>상태</th><th>필수</th><th>필요일</th><th /></tr></thead>
                <tbody>
                  <tr v-for="p in d.plans" :key="p.plan_id">
                    <td class="wrap"><a class="lnk" href="#" data-test="go-plan" :title="`${p.plan_start_dt} ~ ${p.plan_end_dt}`" @click.prevent="navigate('plan-gantt', d.hull_no); emit('close')">{{ p.label }}</a></td><td>{{ codeName('PLANSTAT', p.plan_status) }}</td><td>{{ p.required ? '필수' : '참고' }}</td><td>{{ p.need_dt || '' }}</td>
                    <td class="num"><button v-if="canWrite" class="btn sm dng" @click="removeLink(p)">해제</button></td>
                  </tr>
                  <tr v-if="!d.plans.length"><td colspan="5" class="empty">연계된 공정이 없습니다.</td></tr>
                </tbody>
              </table>
            </div>
            <div v-if="canWrite" class="bar addlink">
              <select v-model="link.plan_id" name="link_plan"><option value="">공정 선택</option><option v-for="p in d.available_plans" :key="p.plan_id" :value="p.plan_id">{{ p.label }}</option></select>
              <label class="chk"><input v-model="link.required" type="checkbox"> 필수</label>
              <button class="btn" data-test="link-add" @click="addLink">연계 추가</button>
            </div>
          </section>
        </template>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
/* Mockup .dwgx: PDF viewer (fills height) + scrollable side column with section cards. */
.dwgx { flex:1; min-height:0; display:grid; grid-template-columns:minmax(0,1fr) minmax(480px,42%); gap:14px; }
.dwgx.solo { grid-template-columns:minmax(0,760px); justify-content:center; }
.dwgx > * { min-height:0; }
.vcard { display:flex; flex-direction:column; margin:0; }
.vcard .sp { flex:1; }
.upl { display:inline-flex; align-items:center; }
.pdfbox { flex:1; min-height:320px; display:flex; border:1px solid var(--line); border-radius:6px; background:#525659; overflow:hidden; }
.pdfbox iframe { flex:1; border:0; background:#fff; }
.pdfmsg { margin:auto; text-align:center; color:#e5e7eb; line-height:1.8; }
.side { overflow:auto; padding-right:2px; }
.side .card:last-child { margin-bottom:0; }
.acts { display:flex; flex-wrap:wrap; align-items:center; gap:8px; }
.acts .note { flex:1; margin:0; }
.tw { max-height:300px; }
.tbl.fit { table-layout:fixed; }
.tbl.fit td, .tbl.fit th { overflow:hidden; text-overflow:ellipsis; }
.tbl td.empty { padding:12px; }
.sub { font-size:11.5px; color:var(--muted); margin-top:1px; }
.addlink { margin:10px 0 0; }
.addlink select { flex:1; min-width:0; }
.chk { display:inline-flex; align-items:center; gap:4px; }
@media (max-width:1100px) {
  .dwgx { display:block; }
  .vcard { margin-bottom:12px; }
  .pdfbox { flex:none; height:60vh; }
  .side { overflow:visible; }
}
</style>
