<script setup>
import { SCREENS } from './registry'

defineProps({ menu: { type: Object, required: true } })
</script>

<template>
  <section class="screen">
    <div class="ph">
      <h2>{{ menu.title }}</h2>
      <span v-if="!menu.can_write" class="badge ro" data-test="readonly">조회 전용</span>
    </div>
    <p class="muted">이 화면은 {{ SCREENS[menu.token] }} 단계에서 구현됩니다.</p>
  </section>
</template>
