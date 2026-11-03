<script setup>
import { toasts } from '../stores/toast'
</script>

<template>
  <div class="toasts" aria-live="polite">
    <div v-for="t in toasts" :key="t.id" :class="['toast', t.kind]" role="status">{{ t.message }}</div>
  </div>
</template>
