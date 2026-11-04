<script setup>
// SHELL-06: detail popups (hull/drawing) — close with Esc or the close button.
import { onBeforeUnmount, watch } from 'vue'

const props = defineProps({ open: Boolean, title: { type: String, default: '' }, large: Boolean, xl: Boolean })
const emit = defineEmits(['close'])

const onKey = (e) => { if (e.key === 'Escape') emit('close') }
watch(() => props.open, (v) => {
  v ? window.addEventListener('keydown', onKey) : window.removeEventListener('keydown', onKey)
}, { immediate: true })
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div v-if="open" class="modal-bg" @click.self="emit('close')">
    <div :class="['modal', { large, xl }]" role="dialog" aria-modal="true" :aria-label="title">
      <header class="modal-h">
        <h3>{{ title }}</h3>
        <button class="btn" data-test="modal-close" @click="emit('close')">닫기 ✕</button>
      </header>
      <div class="modal-b"><slot /></div>
    </div>
  </div>
</template>
