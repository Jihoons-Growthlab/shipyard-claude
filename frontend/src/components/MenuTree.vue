<script setup>
// SHELL-02/03: renders only the menu items the server returned for this user.
import { computed, reactive } from 'vue'

const props = defineProps({ items: { type: Array, required: true }, activeToken: { type: String, default: null } })
const emit = defineEmits(['open'])
const collapsed = reactive({})

const roots = computed(() => props.items.filter((m) => !m.parent_id))
const kids = (id) => props.items.filter((m) => m.parent_id === id)
</script>

<template>
  <nav class="menu">
    <div class="mh">MENU</div>
    <ul>
      <li v-for="r in roots" :key="r.menu_id">
        <a v-if="r.token" :class="['leaf', { on: activeToken === r.token }]" :data-menu="r.menu_id" @click="emit('open', r)"><span class="car">·</span>{{ r.title }}</a>
        <template v-else>
          <a class="grp" :data-group="r.menu_id" @click="collapsed[r.menu_id] = !collapsed[r.menu_id]">
            <span class="car">{{ collapsed[r.menu_id] ? '▶' : '▼' }}</span>{{ r.title }}
          </a>
          <ul v-show="!collapsed[r.menu_id]">
            <li v-for="c in kids(r.menu_id)" :key="c.menu_id">
              <a :class="['leaf', { on: activeToken === c.token }]" :data-menu="c.menu_id" @click="emit('open', c)"><span class="car">·</span>{{ c.title }}</a>
            </li>
          </ul>
        </template>
      </li>
    </ul>
  </nav>
</template>
