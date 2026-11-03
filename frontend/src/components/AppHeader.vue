<script setup>
import { computed } from 'vue'
import WeatherWidget from './WeatherWidget.vue'

const props = defineProps({ user: { type: Object, required: true } })
defineEmits(['logout'])
const groups = computed(() => props.user.groups.map((g) => g.name).join(', ') || '권한 없음')
</script>

<template>
  <header class="hdr">
    <div class="brand">⚓ SWP Shipyard<small>호선 / 공정 / 도면</small></div>
    <div class="sp" />
    <WeatherWidget />
    <div class="usr">
      <div class="nm">{{ user.display_name }} 님</div>
      <div class="grp">{{ groups }} · {{ user.today }}</div>
    </div>
    <button class="btn" data-test="logout" @click="$emit('logout')">로그아웃</button>
  </header>
</template>
