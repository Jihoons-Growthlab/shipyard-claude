<script setup>
// F09 회원관리 (상하 분할): USR-01 목록/필터, USR-02 등록·수정, USR-03 삭제·가입승인. Server enforces M91 Admin + all rules.
import { onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'
import { session } from '../../stores/session'
import { toast } from '../../stores/toast'

const props = defineProps({ menu: { type: Object, required: true } })
const STATUS = { pending: '승인대기', approved: '승인', rejected: '반려', disabled: '중지' }
const BADGE = { pending: 'b-warn', approved: 'b-ok', rejected: 'b-bad', disabled: '' }
const filter = reactive({ status: '', q: '' })
const list = ref({ users: [], total: 0, pending: 0 })
const groups = ref([])
const sel = ref(null)          // emp_no | 'new' | null
const f = reactive({})
const busy = ref(false)
const fail = (e) => toast(e.message, 'e')

async function search() {
  try { list.value = await api.users({ ...filter }) } catch (e) { fail(e) }
}
function reset() { filter.status = ''; filter.q = ''; search() }

function fill(u) {
  Object.assign(f, { emp_no: u.emp_no || '', last_name: u.last_name || '', first_name: u.first_name || '', birth_date: u.birth_date || '',
    phone: u.phone || '', email: u.email || '', password: '', status: u.status || 'approved',
    group: u.groups?.[0]?.code || '', totp_enabled: !!u.totp_enabled, created_at: u.created_at || '' })
}
function pick(u) { sel.value = u.emp_no; fill(u) }
function newUser() { sel.value = 'new'; fill({ status: 'approved', totp_enabled: false }) }

async function save() {
  busy.value = true
  const body = { ...f, group: f.group || null }
  delete body.created_at
  try {
    const u = sel.value === 'new' ? await api.createUser(body) : await api.updateUser(sel.value, body)
    toast('저장되었습니다.', 's')
    pick(u); await search()
    if (u.emp_no === session.user?.emp_no) await session.load()   // 본인 수정 시 헤더/메뉴 갱신
  } catch (e) { fail(e) } finally { busy.value = false }
}

async function remove() {
  if (sel.value === session.user?.emp_no) return toast('로그인 중인 본인 계정은 삭제할 수 없습니다.', 'e')
  if (!confirm(`회원 ${sel.value} 을(를) 삭제합니다.`)) return
  try { await api.deleteUser(sel.value); toast('삭제되었습니다.', 's'); sel.value = null; await search() } catch (e) { fail(e) }
}

async function approve() {
  try {
    await api.approveUser(sel.value, f.group ? [f.group] : [])   // D15: 승인 시 권한 그룹 필수(서버 검증)
    toast(`${f.last_name}${f.first_name} 님의 가입을 승인했습니다.`, 's')
    await search(); const u = list.value.users.find((x) => x.emp_no === sel.value); if (u) pick(u)
  } catch (e) { fail(e) }
}

onMounted(async () => {
  try { groups.value = await api.authGroups() } catch (e) { fail(e) }
  await search()
})
</script>

<template>
  <section class="screen split">
    <div class="ph"><h2>{{ menu.title }}</h2><span class="d">상단 목록 / 하단 입력·수정 (CRUD)</span></div>
    <div class="top-p">
      <div class="bar">
        <select v-model="filter.status" name="status"><option value="">상태 전체</option><option v-for="(n, k) in STATUS" :key="k" :value="k">{{ n }}</option></select>
        <input v-model="filter.q" name="q" placeholder="아이디/이름/이메일/전화" @keyup.enter="search">
        <button class="btn pri" data-test="search" @click="search">조회</button>
        <button class="btn" data-test="reset" @click="reset">초기화</button>
        <span class="note right" data-test="counts">{{ list.total }}명 · 승인대기 {{ list.pending }}명</span>
      </div>
      <div class="tw"><table class="tbl" data-test="users">
        <thead><tr><th>아이디</th><th>이름</th><th>이메일</th><th>전화번호</th><th>생년월일</th><th>상태</th><th>2차인증</th><th>권한그룹</th><th>가입일</th></tr></thead>
        <tbody>
          <tr v-for="u in list.users" :key="u.emp_no" :data-id="u.emp_no" :class="{ sel: sel === u.emp_no }" @click="pick(u)">
            <td><b>{{ u.emp_no }}</b></td><td>{{ u.display_name }}</td><td>{{ u.email }}</td><td>{{ u.phone }}</td><td>{{ u.birth_date }}</td>
            <td><span :class="['bdg', BADGE[u.status]]">{{ STATUS[u.status] }}</span></td>
            <td>{{ u.totp_enabled ? '사용' : '-' }}</td><td>{{ u.groups.map((g) => g.name).join(', ') || '-' }}</td><td>{{ u.created_at }}</td>
          </tr>
        </tbody>
      </table></div>
    </div>

    <div class="bot-p card">
      <h3>{{ sel === 'new' ? '회원 등록' : sel ? `회원 수정 — ${f.last_name}${f.first_name}` : '입력 / 수정' }}</h3>
      <form v-if="sel" class="grid g4" autocomplete="off" data-test="form" @submit.prevent="save">
        <label>성 *<input v-model="f.last_name" name="last_name"></label>
        <label>이름 *<input v-model="f.first_name" name="first_name"></label>
        <label>생년월일 *<input v-model="f.birth_date" name="birth_date" type="date"></label>
        <label>전화번호 *<input v-model="f.phone" name="phone" placeholder="010-0000-0000"></label>
        <label class="span2">이메일 *<input v-model="f.email" name="email" type="email"></label>
        <label>아이디 *<input v-model="f.emp_no" name="emp_no" :readonly="sel !== 'new'"></label>
        <label>{{ sel === 'new' ? '비밀번호 *' : '비밀번호 (변경 시만 입력)' }}<input v-model="f.password" name="password" type="password" autocomplete="new-password" placeholder="8자 이상"></label>
        <label>상태<select v-model="f.status" name="ustatus"><option v-for="(n, k) in STATUS" :key="k" :value="k">{{ n }}</option></select></label>
        <label>권한 그룹<select v-model="f.group" name="group"><option value="">없음</option><option v-for="g in groups" :key="g.code" :value="g.code">{{ g.name }}</option></select></label>
        <label>구글 2차인증<span class="ck"><input v-model="f.totp_enabled" name="totp" type="checkbox"> 사용 (등록된 사용자만)</span></label>
        <label>가입일<input :value="f.created_at || '-'" readonly></label>
      </form>
      <div v-else class="empty">목록에서 회원을 선택하거나 [신규]를 누르세요.</div>
      <div v-if="menu.can_write" class="bar">
        <button class="btn" data-test="new" @click="newUser">신규</button>
        <button class="btn pri" data-test="save" :disabled="!sel || busy" @click="save">저장</button>
        <button class="btn dng" data-test="delete" :disabled="!sel || sel === 'new'" @click="remove">삭제</button>
        <button v-if="sel && sel !== 'new' && f.status === 'pending'" class="btn ok" data-test="approve" @click="approve">가입 승인</button>
      </div>
    </div>
  </section>
</template>
