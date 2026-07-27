<script setup lang="ts">
import { onMounted, ref } from 'vue'

type ClosePreference = 'ask' | 'tray' | 'quit'

const options: Array<{ value: ClosePreference; title: string; desc: string }> = [
  {
    value: 'ask',
    title: '每次询问',
    desc: '关闭窗口时弹出选择：最小化到托盘或退出程序'
  },
  {
    value: 'tray',
    title: '最小化到托盘',
    desc: '关闭窗口后隐藏到系统托盘，API 继续在后台运行'
  },
  {
    value: 'quit',
    title: '直接退出',
    desc: '关闭窗口即退出程序并停止本地服务'
  }
]

const closeAction = ref<ClosePreference>('ask')
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const savedHint = ref('')
const hasBridge = ref(false)

async function loadPrefs() {
  loading.value = true
  error.value = ''
  savedHint.value = ''
  try {
    const bridge = window.lotteryDesktop
    if (!bridge?.getWindowPrefs) {
      hasBridge.value = false
      error.value = '当前环境无桌面桥接，窗口设置仅在 Electron 打包/开发客户端中可用'
      return
    }
    hasBridge.value = true
    const prefs = await bridge.getWindowPrefs()
    closeAction.value = prefs.closeAction
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function select(action: ClosePreference) {
  if (!hasBridge.value || saving.value || closeAction.value === action) return
  saving.value = true
  error.value = ''
  savedHint.value = ''
  try {
    const prefs = await window.lotteryDesktop!.setWindowPrefs({ closeAction: action })
    closeAction.value = prefs.closeAction
    savedHint.value = '已保存'
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void loadPrefs()
})
</script>

<template>
  <section class="page">
    <div class="page-head">
      <div>
        <h1>设置</h1>
        <p class="lead">窗口关闭行为 · 可随时改回「每次询问」</p>
      </div>
      <div class="panel-id">SETTINGS</div>
    </div>

    <div class="panel">
      <div class="panel-hd">
        <span>关闭窗口时</span>
        <span v-if="savedHint" class="muted">{{ savedHint }}</span>
        <span v-else-if="loading" class="muted">读取中…</span>
        <span v-else-if="saving" class="muted">保存中…</span>
      </div>
      <div class="panel-bd">
        <div class="settings-options">
          <button
            v-for="opt in options"
            :key="opt.value"
            type="button"
            class="settings-option"
            :class="{ active: closeAction === opt.value }"
            :disabled="!hasBridge || loading || saving"
            @click="select(opt.value)"
          >
            <div class="settings-option__title">{{ opt.title }}</div>
            <div class="settings-option__desc">{{ opt.desc }}</div>
          </button>
        </div>
        <p class="muted" style="margin-top: 12px">
          托盘模式下可从菜单栏/托盘图标恢复窗口；勾选「不再提示」也会写入此处同一项设置。
        </p>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
  </section>
</template>

<style scoped>
.settings-options {
  display: grid;
  gap: 10px;
}

.settings-option {
  text-align: left;
  padding: 12px 14px;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text);
  cursor: pointer;
  border-radius: 6px;
  font-family: var(--sans);
}

.settings-option:hover:not(:disabled) {
  border-color: var(--line-strong);
  background: var(--bg-3);
}

.settings-option.active {
  border-color: var(--gold-dim);
  box-shadow: inset 3px 0 0 var(--gold);
}

.settings-option:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.settings-option__title {
  font-size: 14px;
  font-weight: 600;
}

.settings-option__desc {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-dim);
  line-height: 1.45;
}
</style>
