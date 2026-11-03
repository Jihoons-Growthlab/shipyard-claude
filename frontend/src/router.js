import { createRouter, createWebHistory } from 'vue-router'
import AuthView from './views/AuthView.vue'
import ShellView from './views/ShellView.vue'
import { session } from './stores/session'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: AuthView },
    { path: '/', component: ShellView, meta: { requiresAuth: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !session.token) return '/login'
  if (to.path === '/login' && session.token) return '/'
})

session.onExpired = () => router.replace('/login')
