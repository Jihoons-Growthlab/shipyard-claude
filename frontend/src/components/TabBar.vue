<script setup>
defineProps({ tabs: { type: Array, required: true }, active: { type: String, default: null } })
defineEmits(['activate', 'close', 'close-others'])
</script>

<template>
  <div class="tabs" role="tablist">
    <div v-for="t in tabs" :key="t.key" :class="['tab', { on: t.key === active }]" role="tab" :data-key="t.key" @click="$emit('activate', t.key)">
      <span>{{ t.title }}</span>
      <button class="x" aria-label="탭 닫기" @click.stop="$emit('close', t.key)">×</button>
    </div>
    <button v-if="tabs.length > 1" class="btn sm" data-test="close-others" @click="$emit('close-others', active)">다른 탭 닫기</button>
  </div>
</template>
