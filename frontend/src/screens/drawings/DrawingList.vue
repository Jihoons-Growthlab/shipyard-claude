<script setup>
// F07 DWG-01: drawing list with hull/discipline/status/keyword filters; Rev = CurrentRevNo (+ latest rev if different).
import { inject, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../../api/client'
import { codeList, codeName, loadCodes } from '../../stores/codes'
import { toast } from '../../stores/toast'
import DrawingDetailModal from './DrawingDetailModal.vue'

const props = defineProps({ menu: { type: Object, required: true }, param: { type: String, default: null } })
const f = reactive({ hull_no: props.param || '', discipline: '', status: '', q: '' }) // param = hull filter (mockup gotoList)
const hulls = ref([])
const rows = ref([])
const detail = ref(null) // drawing_id | 'new' | null

async function search() {
  try { rows.value = await api.drawings({ ...f }) } catch (e) { toast(e.message, 'e') }
}
function reset() { Object.assign(f, { hull_no: '', discipline: '', status: '', q: '' }); search() }

onMounted(async () => {
  try {
    await loadCodes()
    hulls.value = await api.hulls().catch(() => [])
    await search()
  } catch (e) { toast(e.message, 'e') }
})

const navRequest = inject('navRequest', ref({}))
watch(navRequest, (r) => { if (r.token === 'dwg-list' && props.param && r.param === props.param) { Object.assign(f, { hull_no: r.param, discipline: '', status: '', q: '' }); search() } })

async function onSaved(id) { detail.value = id; await search() }
async function onDeleted() { detail.value = null; await search() }
defineExpose({ f, rows, detail, search })
</script>

<template>
  <section class="screen dwg">
    <div class="ph">
      <h2>{{ menu.title }}</h2>
      <span class="d">행 더블클릭 또는 [상세]로 도면 상세·PDF 뷰어·리비전·결재 팝업을 엽니다. Rev는 현재 배포(유효) 리비전입니다.</span>
      <span v-if="!menu.can_write" class="badge ro" data-test="readonly">조회 전용</span>
    </div>
    <div class="bar">
      <select v-model="f.hull_no" name="hull_no"><option value="">호선 전체</option><option v-for="h in hulls" :key="h.hull_no" :value="h.hull_no">{{ h.hull_no }} {{ h.hull_nm }}</option></select>
      <select v-model="f.discipline" name="discipline"><option value="">분야 전체</option><option v-for="c in codeList('DWGDISC')" :key="c.code" :value="c.code">{{ c.name }}</option></select>
      <select v-model="f.status" name="status"><option value="">상태 전체</option><option v-for="c in codeList('DWGSTAT')" :key="c.code" :value="c.code">{{ c.name }}</option></select>
      <input v-model="f.q" name="q" placeholder="도면번호/도면명" @keyup.enter="search">
      <button class="btn pri" data-test="search" @click="search">조회</button>
      <button class="btn" @click="reset">초기화</button>
      <button v-if="menu.can_write" class="btn pri right" data-test="new" @click="detail = 'new'">+ 도면 등록</button>
    </div>
    <table class="tbl" data-test="drawings">
      <thead><tr><th>도면번호</th><th>도면명</th><th>호선</th><th>블록</th><th>분야</th><th>Rev</th><th>상태</th><th>설계자</th><th>연계공정</th><th /></tr></thead>
      <tbody>
        <tr v-for="d in rows" :key="d.drawing_id" :data-id="d.drawing_id" @dblclick="detail = d.drawing_id">
          <td><b>{{ d.drawing_no }}</b></td><td>{{ d.drawing_nm }}</td><td>{{ d.hull_no }}</td><td>{{ d.block_cd || '-' }}</td>
          <td>{{ codeName('DWGDISC', d.discipline) }}</td>
          <td data-test="rev">Rev{{ d.current_rev_no }}<span v-if="d.latest_rev_no !== d.current_rev_no" class="muted"> (최신 Rev{{ d.latest_rev_no }})</span></td>
          <td><span :class="['bdg', 'd-' + d.dwg_status.toLowerCase()]">{{ codeName('DWGSTAT', d.dwg_status) }}</span></td><td>{{ d.designer_nm || '' }}</td>
          <td class="num">{{ d.link_count || '-' }}</td>
          <td><button class="btn sm" @click="detail = d.drawing_id">상세</button></td>
        </tr>
      </tbody>
    </table>
    <div class="note">총 {{ rows.length }}건</div>
    <DrawingDetailModal v-if="detail" :drawing-id="detail" :can-write="menu.can_write"
                        @close="detail = null" @saved="onSaved" @deleted="onDeleted" @changed="search" />
  </section>
</template>
