<script setup lang="ts">
import { ref, watch } from 'vue'

const open = defineModel<boolean>('open', { default: false })

const remember = ref(false)

watch(open, (v) => {
  if (v) remember.value = false
})

const emit = defineEmits<{
  decide: [action: 'tray' | 'quit' | 'cancel', remember: boolean]
}>()

function choose(action: 'tray' | 'quit' | 'cancel') {
  emit('decide', action, remember.value)
  open.value = false
}

function onOverlayClick() {
  choose('cancel')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="close-overlay" role="presentation" @click.self="onOverlayClick">
      <div
        class="close-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="close-dialog-title"
        @keydown.esc.prevent="choose('cancel')"
      >
        <h2 id="close-dialog-title" class="close-dialog__title">关闭窗口后如何处理？</h2>
        <p class="close-dialog__desc">可最小化到系统托盘在后台运行，或直接退出程序。</p>

        <label class="close-dialog__remember">
          <input v-model="remember" type="checkbox" />
          <span>不再提示，记住本次选择</span>
        </label>

        <div class="close-dialog__actions">
          <button type="button" class="close-btn close-btn--primary" @click="choose('tray')">
            最小化到托盘
          </button>
          <button type="button" class="close-btn" @click="choose('quit')">退出程序</button>
          <button type="button" class="close-btn" @click="choose('cancel')">取消</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.close-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  padding: 24px;
  background: color-mix(in srgb, #000 35%, transparent);
}

.close-dialog {
  width: min(420px, 100%);
  padding: 22px 22px 18px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--bg-1) 92%, #f0f0f0);
  border: 1px solid var(--line-strong);
  box-shadow: 0 16px 40px color-mix(in srgb, #000 28%, transparent);
  color: var(--text);
  font-family: var(--sans);
}

.close-dialog__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.close-dialog__desc {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-dim);
}

.close-dialog__remember {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  font-size: 13px;
  color: var(--text-dim);
  cursor: pointer;
  user-select: none;
}

.close-dialog__remember input {
  width: 15px;
  height: 15px;
  accent-color: var(--text);
  cursor: pointer;
}

.close-dialog__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

.close-btn {
  height: 34px;
  padding: 0 14px;
  border-radius: 6px;
  border: 1px solid var(--line-strong);
  background: var(--bg-2);
  color: var(--text);
  font-size: 13px;
  font-family: var(--sans);
  cursor: pointer;
}

.close-btn:hover {
  background: var(--bg-3);
}

.close-btn--primary {
  border-color: transparent;
  background: #2a2a2a;
  color: #f5f5f5;
}

.close-btn--primary:hover {
  background: #1a1a1a;
}

html[data-theme='terminal'] .close-btn--primary {
  background: var(--btn-a);
  color: var(--btn-fg);
  border: 1px solid var(--gold-dim);
}

html[data-theme='terminal'] .close-btn--primary:hover {
  background: var(--btn-b);
}
</style>
