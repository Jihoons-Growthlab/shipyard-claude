<script setup>
// F08 결재함: APV-01 내 결재 대기, APV-02 승인/반려, APV-03 배포 대기, APV-04 최근 이력.
// Server enforces D11 (assigned current approver / M31 Write + completed approval); buttons here are hints only.
import { onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'
import { session } from '../../stores/session'
import { toast } from '../../stores/toast'
import DrawingDetailModal from '../drawings/DrawingDetailModal.vue'

const props = defineProps({ menu: { type: Object, required: true } })
const box = ref({ waiting: [], ready: [], can_issue: false })
const hist = ref([])
const comments = reactive({})
const detail = ref(null)
const busy = ref(false)
const step = (n) => (n === 1 ? '검토' : '승인')

async function load() {
  try {
    const [b, h] = await Promise.all([api.approvalInbox(), api.approvalHistory()])
    box.value = b; hist.value = h
  } catch (e) { toast(e.message, 'e') }
}

async function decide(a, result) {
  const cm = (comments[a.approval_id] || '').trim()
  if (result === 'REJECT' && !cm) return toast('반려 시 의견을 입력하세요.', 'e')
  busy.value = true
  try {
    await api.decideApproval(a.approval_id, result, cm)
    toast(result === 'APPROVE' ? '승인했습니다.' : '반려했습니다. 도면은 작성중으로 되돌려집니다.', 's')
    delete comments[a.approval_id]
    await load()
  } catch (e) { toast(e.message, 'e'); await load() } finally { busy.value = false }
}

async function issue(d) {
  busy.value = true
  try {
    await api.issueRevision(d.drawing_id, d.rev_no)
    toast('도면이 배포되었습니다. 연계 공정 상태가 갱신됩니다.', 's')
    await load()
  } catch (e) { toast(e.message, 'e'); await load() } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <section class="screen">
    <div class="ph"><h2>도면 결재함</h2><span class="d">{{ session.user?.display_name || session.user?.emp_no }} 님의 결재 대기와 배포 대기 도면입니다.</span></div>

    <div class="card">
      <h3>내 결재 대기 <span class="bdg b-warn" data-test="wait-count">{{ box.waiting.length }}</span></h3>
      <table class="tbl" data-test="waiting">
        <thead><tr><th>도면번호</th><th>도면명</th><th>Rev</th><th>단계</th><th>변경사유</th><th>의견</th><th /></tr></thead>
        <tbody>
          <tr v-for="a in box.waiting" :key="a.approval_id" :data-id="a.approval_id">
            <td><a class="lnk" href="#" @click.prevent="detail = a.drawing_id">{{ a.drawing_no }}</a></td>
            <td>{{ a.drawing_nm }}</td><td>Rev{{ a.rev_no }}</td><td>{{ step(a.step_no) }}</td>
            <td class="wrap">{{ a.change_desc || '' }}</td>
            <td><input v-model="comments[a.approval_id]" class="in" name="comment" placeholder="의견 (반려 시 필수)"></td>
            <td v-if="menu.can_write">
              <button class="btn sm ok" data-test="approve" :disabled="busy" @click="decide(a, 'APPROVE')">승인</button>
              <button class="btn sm dng" data-test="reject" :disabled="busy" @click="decide(a, 'REJECT')">반려</button>
            </td><td v-else />
          </tr>
          <tr v-if="!box.waiting.length"><td colspan="7" class="muted">결재 대기 건이 없습니다.</td></tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h3>배포 대기 (승인 완료) <span class="bdg b-info">{{ box.ready.length }}</span></h3>
      <table class="tbl" data-test="ready">
        <thead><tr><th>도면번호</th><th>도면명</th><th>Rev</th><th>배포 시 착수 가능해질 수 있는 공정</th><th /></tr></thead>
        <tbody>
          <tr v-for="d in box.ready" :key="d.drawing_id" :data-id="d.drawing_id">
            <td><a class="lnk" href="#" @click.prevent="detail = d.drawing_id">{{ d.drawing_no }}</a></td>
            <td>{{ d.drawing_nm }}</td><td>Rev{{ d.rev_no }}</td>
            <td>{{ d.effect_plans.join(', ') || '-' }}</td>
            <td><button v-if="box.can_issue" class="btn sm ok" data-test="issue" :disabled="busy" @click="issue(d)">배포</button></td>
          </tr>
          <tr v-if="!box.ready.length"><td colspan="5" class="muted">배포 대기 도면이 없습니다.</td></tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h3>최근 결재 이력</h3>
      <table class="tbl" data-test="history">
        <thead><tr><th>일시</th><th>도면번호</th><th>Rev</th><th>단계</th><th>결재자</th><th>결과</th><th>의견</th></tr></thead>
        <tbody>
          <tr v-for="h in hist" :key="h.approval_id">
            <td>{{ h.act_dt || '' }}</td><td>{{ h.drawing_no }}</td><td>Rev{{ h.rev_no }}</td><td>{{ step(h.step_no) }}</td>
            <td>{{ h.approver_nm || h.approver_emp_no || '' }}</td>
            <td><span :class="['bdg', h.result === 'APPROVE' ? 'b-ok' : 'b-bad']">{{ h.result === 'APPROVE' ? '승인' : '반려' }}</span></td>
            <td>{{ h.comment || '' }}</td>
          </tr>
          <tr v-if="!hist.length"><td colspan="7" class="muted" data-test="history-empty">결재 이력이 없습니다.</td></tr>
        </tbody>
      </table>
    </div>

    <DrawingDetailModal v-if="detail" :drawing-id="detail" :can-write="box.can_issue"
                        @close="detail = null" @changed="load" @deleted="detail = null; load()" />
  </section>
</template>
