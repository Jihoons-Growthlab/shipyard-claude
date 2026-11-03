<script setup>
// F01: login / OTP / sign-up. All validation is re-done on the server; messages come from the API.
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
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
    <form v-if="mode === 'login'" class="card" @submit.prevent="doLogin">
      <h1>SWP Shipyard</h1>
      <label>아이디<input v-model="login.emp_no" name="emp_no" autocomplete="username" autofocus /></label>
      <label>비밀번호<input v-model="login.password" name="password" type="password" autocomplete="current-password" /></label>
      <div class="err">{{ err }}</div>
      <button class="btn pri block" :disabled="busy">로그인</button>
      <a class="lnk" @click="go('signup')">회원가입</a>
    </form>

    <form v-else-if="mode === 'otp'" class="card" @submit.prevent="doOtp">
      <h1>2차 인증</h1>
      <p class="muted">Authenticator 앱의 6자리 코드를 입력하세요.</p>
      <label>인증 코드<input v-model="otp.code" name="otp" inputmode="numeric" maxlength="6" autocomplete="one-time-code" autofocus /></label>
      <div class="err">{{ err }}</div>
      <button class="btn pri block" :disabled="busy">확인</button>
      <a class="lnk" @click="go('login')">← 로그인으로</a>
    </form>

    <form v-else class="card wide" @submit.prevent="doSignup">
      <h1>회원가입</h1>
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
      <a class="lnk" @click="go('login')">← 로그인으로</a>
    </form>
  </div>
</template>
