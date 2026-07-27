<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getApiBaseUrl, setApiBaseUrl } from './api/client'
import { applyTheme, loadTheme } from './themes'
import logoUrl from './assets/logo.png'

type ApiStatus = { ready: boolean; baseUrl: string; error: string }

const nav = [
  { path: '/draws', code: '01', label: '开奖行情' },
  { path: '/analyze', code: '02', label: '因子分析' },
  { path: '/predict', code: '03', label: '信号生成' },
  { path: '/ticket', code: '04', label: '下一期选号' },
  { path: '/backtest', code: '05', label: '回测台' },
  { path: '/check', code: '06', label: '中奖核对' },
  { path: '/themes', code: '07', label: '界面主题' }
]

const route = useRoute()
const router = useRouter()
const status = ref<ApiStatus>({ ready: false, baseUrl: getApiBaseUrl(), error: '' })
const clock = ref('')
const apiBusy = ref(false)
let off: (() => void) | undefined
let timer: number | undefined

const readyText = computed(() => (status.value.ready ? 'LIVE' : status.value.error ? 'DOWN' : 'SYNC'))
const connClass = computed(() => ({
  ok: status.value.ready,
  bad: !status.value.ready && !!status.value.error
}))
const apiToggleLabel = computed(() => (status.value.ready ? '关闭服务' : '启动服务'))
const hasDesktopBridge = computed(() => !!window.lotteryDesktop)

function tick() {
  const d = new Date()
  clock.value = d.toLocaleString('zh-CN', { hour12: false })
}

function applyStatus(s: ApiStatus) {
  status.value = s
  setApiBaseUrl(s.baseUrl)
}

async function toggleApi() {
  const bridge = window.lotteryDesktop
  if (!bridge || apiBusy.value) return
  apiBusy.value = true
  try {
    const next = status.value.ready ? await bridge.stopApi() : await bridge.startApi()
    applyStatus(next)
  } catch (e) {
    status.value = {
      ...status.value,
      ready: false,
      error: e instanceof Error ? e.message : String(e)
    }
  } finally {
    apiBusy.value = false
  }
}

onMounted(async () => {
  applyTheme(loadTheme())
  tick()
  timer = window.setInterval(tick, 1000)
  const bridge = window.lotteryDesktop
  if (bridge) {
    applyStatus(await bridge.getApiStatus())
    off = bridge.onApiStatus(applyStatus)
  } else {
    status.value = { ready: true, baseUrl: getApiBaseUrl(), error: '' }
  }
})

onUnmounted(() => {
  off?.()
  if (timer) window.clearInterval(timer)
})
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand-lockup">
        <img class="brand-logo" :src="logoUrl" alt="" width="22" height="22" />
        <div class="brand-mark">Aether</div>
        <div class="brand-title">双色球 / 大乐透 · 彩票量化</div>
      </div>
      <div class="ticker" aria-label="运行状态">
        <div class="ticker-item" title="双色球单式：红球 6 个 + 蓝球 1 个">
          <span class="ticker-k">双色球</span>
          <span class="ticker-v">红6+蓝1</span>
        </div>
        <div class="ticker-item" title="大乐透单式：前区 5 个 + 后区 2 个">
          <span class="ticker-k">大乐透</span>
          <span class="ticker-v">前5+后2</span>
        </div>
        <div class="ticker-item" title="仅供研究娱乐，不构成投注建议">
          <span class="ticker-k">运行模式</span>
          <span class="ticker-v">研究</span>
        </div>
        <div class="ticker-item down" title="尚未验证相对随机是否有超额收益">
          <span class="ticker-k">Edge</span>
          <span class="ticker-v">未验证</span>
        </div>
        <div class="ticker-item up" title="开奖数据保存在本地 CSV">
          <span class="ticker-k">数据源</span>
          <span class="ticker-v">本地 CSV</span>
        </div>
      </div>
      <div class="conn" :class="connClass">
        <span class="conn-dot" />
        <span>{{ readyText }}</span>
        <button
          class="api-toggle"
          type="button"
          :disabled="apiBusy || !hasDesktopBridge"
          :title="status.error || (status.ready ? '停止本地 FastAPI' : '启动本地 FastAPI')"
          @click="toggleApi"
        >
          {{ apiBusy ? '…' : apiToggleLabel }}
        </button>
        <span>{{ clock }}</span>
      </div>
    </header>

    <div class="workspace">
      <aside class="rail">
        <div class="rail-label">工作区</div>
        <button
          v-for="item in nav"
          :key="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
          @click="router.push(item.path)"
        >
          <span class="nav-code">{{ item.code }}</span>
          <span class="nav-name">{{ item.label }}</span>
        </button>
      </aside>

      <main class="content">
        <router-view />
      </main>
    </div>

    <footer class="statusbar">
      <span>Aether · RESEARCH ONLY</span>
      <span>仅供研究娱乐 · 开奖随机 · <em>不构成投注建议</em></span>
    </footer>
  </div>
</template>
