<script setup>
// F01: login / OTP / sign-up. All validation is re-done on the server; messages come from the API.
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import AuthScene from '../components/AuthScene.vue'
import { session } from '../stores/session'
import { toast } from '../stores/toast'

const router = useRouter()
const mode = ref('login')
const err = ref('')
const busy = ref(false)
const login = reactive({ emp_no: '', password: '' })
const otp = reactive({ token: null, code: '' })
const blank = () => ({ last_name: '', first_name: '', birth_date: '', phone: '', email: '', emp_no: '', password: '', password_confirm: '' })
const signup = reactive(blank())
const FEATURES = [['호선', '호선별 진척률과 인도 일정을 한눈에'], ['공정', '간트 계획부터 일별 실적까지'], ['도면', '리비전·결재·배포 이력 관리']]

const go = (m) => { mode.value = m; err.value = '' }
async function run(fn) {
  busy.value = true; err.value = ''
  try { await fn() } catch (e) { err.value = e.message } finally { busy.value = false }
}
const enter = async (res) => { session.setToken(res.access_token); await router.replace('/') }

const doLogin = () => run(async () => {
  const res = await api.login(login.emp_no.trim(), login.password)
  if (res.otp_required) { otp.token = res.otp_token; otp.code = ''; go('otp') } else await enter(res)
})
const doOtp = () => run(async () => { await enter(await api.verifyOtp(otp.token, otp.code.trim())); otp.token = null })
const doSignup = () => run(async () => {
  await api.register({ ...signup })
  Object.assign(signup, blank()); go('login')
  toast('가입 신청 완료. 관리자 승인 후 로그인할 수 있습니다.', 's')
})
</script>

<template>
  <div class="auth">
    <AuthScene />
    <aside class="auth-brand">
      <div class="eyebrow"><span>⚓</span> SWP SHIPYARD</div>
      <p class="lead">설계부터 인도까지,<br>조선소 운영을 한곳에서</p>
      <ul>
        <li v-for="[t, d] in FEATURES" :key="t"><b>{{ t }}</b><span>{{ d }}</span></li>
      </ul>
    </aside>
    <form v-if="mode === 'login'" class="card" @submit.prevent="doLogin">
      <div class="logo">SWP SHIPYARD</div>
      <h1>조선소 통합관리</h1>
      <div class="sub">호선 · 공정 · 도면 관리 시스템</div>
      <label>아이디<input v-model="login.emp_no" name="emp_no" autocomplete="username" autofocus /></label>
      <label>비밀번호<input v-model="login.password" name="password" type="password" autocomplete="current-password" /></label>
      <div class="err">{{ err }}</div>
      <button class="btn pri block" :disabled="busy">로그인</button>
      <div class="links"><a class="lnk" @click="go('signup')">회원가입</a><span class="muted">구글 2차 인증 사용 계정은 다음 단계에서 OTP 입력</span></div>
    </form>

    <form v-else-if="mode === 'otp'" class="card" @submit.prevent="doOtp">
      <div class="logo">2-STEP VERIFICATION</div>
      <h1>구글 2차 인증</h1>
      <div class="sub">Google Authenticator 앱에 표시된 6자리 코드를 입력하세요.</div>
      <label>인증 코드<input v-model="otp.code" class="otp" name="otp" inputmode="numeric" maxlength="6" autocomplete="one-time-code" autofocus /></label>
      <div class="err">{{ err }}</div>
      <button class="btn pri block" :disabled="busy">확인</button>
      <div class="links"><a class="lnk" @click="go('login')">← 로그인으로</a></div>
    </form>

    <form v-else class="card wide" @submit.prevent="doSignup">
      <div class="logo">SIGN UP</div>
      <h1>회원가입</h1>
      <div class="sub">가입 후 관리자 승인이 완료되면 로그인할 수 있습니다.</div>
      <div class="g2">
        <label>성<input v-model="signup.last_name" /></label>
        <label>이름<input v-model="signup.first_name" /></label>
        <label>생년월일<input v-model="signup.birth_date" type="date" /></label>
        <label>전화번호<input v-model="signup.phone" placeholder="010-0000-0000" /></label>
        <label>이메일<input v-model="signup.email" type="email" /></label>
        <label>아이디<input v-model="signup.emp_no" autocomplete="username" /></label>
        <label>비밀번호<input v-model="signup.password" type="password" autocomplete="new-password" /></label>
        <label>비밀번호 확인<input v-model="signup.password_confirm" type="password" autocomplete="new-password" /></label>
      </div>
      <div class="err">{{ err }}</div>
      <button class="btn pri block" :disabled="busy">가입 신청</button>
      <div class="links"><a class="lnk" @click="go('login')">← 로그인으로</a></div>
    </form>
  </div>
</template>
