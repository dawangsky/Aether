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
  { path: '/backtest', code: '04', label: '回测台' },
  { path: '/check', code: '05', label: '中奖核对' },
  { path: '/themes', code: '06', label: '界面主题' }
]

const route = useRoute()
const router = useRouter()
const status = ref<ApiStatus>({ ready: false, baseUrl: getApiBaseUrl(), error: '' })
const clock = ref('')
let off: (() => void) | undefined
let timer: number | undefined

const readyText = computed(() => (status.value.ready ? 'LIVE' : status.value.error ? 'DOWN' : 'SYNC'))
const connClass = computed(() => ({
  ok: status.value.ready,
  bad: !status.value.ready && !!status.value.error
}))

function tick() {
  const d = new Date()
  clock.value = d.toLocaleString('zh-CN', { hour12: false })
}

onMounted(async () => {
  applyTheme(loadTheme())
  tick()
  timer = window.setInterval(tick, 1000)
  const bridge = window.lotteryDesktop
  if (bridge) {
    const s = await bridge.getApiStatus()
    status.value = s
    setApiBaseUrl(s.baseUrl)
    off = bridge.onApiStatus((next) => {
      status.value = next
      setApiBaseUrl(next.baseUrl)
    })
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
      <div class="ticker">
        <span><strong>SSQ</strong> 红6+蓝1</span>
        <span><strong>DLT</strong> 前5+后2</span>
        <span><strong>MODE</strong> 研究模式</span>
        <span class="down"><strong>EDGE</strong> 未验证</span>
        <span class="up"><strong>DATA</strong> 本地 CSV</span>
      </div>
      <div class="conn" :class="connClass">
        <span class="conn-dot" />
        <span>{{ readyText }}</span>
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
