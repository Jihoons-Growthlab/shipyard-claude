<script setup>
// F04 HULL-01: list + filters; double-click/상세 opens detail popup (inherits M11).
import { onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'
import { codeList, codeName, loadCodes } from '../../stores/codes'
import { toast } from '../../stores/toast'
import HullDetailModal from './HullDetailModal.vue'

const props = defineProps({ menu: { type: Object, required: true } })
const f = reactive({ status: '', ship_type: '', q: '' })
const rows = ref([])
const sel = ref(null)
const detail = ref(null) // hull_no | 'new' | null

async function search() {
  try { rows.value = await api.hulls({ ...f }) } catch (e) { toast(e.message, 'e') }
}
function reset() { Object.assign(f, { status: '', ship_type: '', q: '' }); search() }
function onSaved(no) { search(); if (no) { detail.value = no; sel.value = no } }
function onDeleted() { detail.value = null; sel.value = null; search() }

onMounted(async () => { await loadCodes().catch((e) => toast(e.message, 'e')); search() })
defineExpose({ search })
</script>

<template>
  <section class="screen">
    <div class="ph">
      <h2>{{ menu.title }}</h2>
      <span v-if="!menu.can_write" class="badge ro" data-test="readonly">조회 전용</span>
    </div>
    <p class="muted">행을 더블클릭하거나 [상세]를 누르면 호선 상세 팝업이 열립니다.</p>
    <form class="bar" @submit.prevent="search">
      <select v-model="f.status" name="status"><option value="">상태 전체</option><option v-for="c in codeList('HULLSTAT')" :key="c.code" :value="c.code">{{ c.name }}</option></select>
      <select v-model="f.ship_type" name="ship_type"><option value="">선종 전체</option><option v-for="c in codeList('SHIPTYPE')" :key="c.code" :value="c.code">{{ c.name }}</option></select>
      <input v-model="f.q" name="q" placeholder="호선번호/호선명/선주" />
      <button class="btn pri" data-test="search">조회</button>
      <button class="btn" type="button" data-test="reset" @click="reset">초기화</button>
      <button v-if="menu.can_write" class="btn pri right" type="button" data-test="new-hull" @click="detail = 'new'">+ 호선 등록</button>
    </form>
    <table class="tbl">
      <thead><tr><th>호선번호</th><th>호선명</th><th>선종</th><th>상태</th><th>선주</th><th>선급</th><th>도크</th><th>계약일</th><th>인도예정</th><th>진척률</th><th>지연</th><th></th></tr></thead>
      <tbody>
        <tr v-for="h in rows" :key="h.hull_no" :class="{ sel: sel === h.hull_no }" :data-hull="h.hull_no"
            @click="sel = h.hull_no" @dblclick="detail = h.hull_no">
          <td><b>{{ h.hull_no }}</b></td><td>{{ h.hull_nm }}</td><td>{{ codeName('SHIPTYPE', h.ship_type) }}</td>
          <td>{{ codeName('HULLSTAT', h.hull_status) }}</td><td>{{ h.owner_nm }}</td><td>{{ h.class_society }}</td>
          <td>{{ h.dock_no || '-' }}</td><td>{{ h.contract_dt }}</td><td>{{ h.delivery_dt }}</td>
          <td>{{ h.progress === null ? '계획 없음' : h.progress + '%' }}</td><td class="num">{{ h.delay_count || '-' }}</td>
          <td><button class="btn sm" data-test="open" @click.stop="detail = h.hull_no">상세</button></td>
        </tr>
        <tr v-if="!rows.length"><td colspan="12" class="muted">조회된 호선이 없습니다.</td></tr>
      </tbody>
    </table>
    <div class="muted">총 {{ rows.length }}척</div>
    <HullDetailModal v-if="detail" :hull-no="detail" :can-write="menu.can_write"
                     @close="detail = null" @saved="onSaved" @deleted="onDeleted" @changed="search" />
  </section>
</template>
