<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getApiBaseUrl, setApiBaseUrl } from './api/client'

type ApiStatus = { ready: boolean; baseUrl: string; error: string }

const nav = [
  { path: '/draws', code: '01', label: '行情开奖' },
  { path: '/analyze', code: '02', label: '因子分析' },
  { path: '/predict', code: '03', label: '信号生成' },
  { path: '/backtest', code: '04', label: '回测台' }
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
        <div class="brand-mark">LQ Terminal</div>
        <div class="brand-title">双色球 / 大乐透 · 本地量化终端</div>
      </div>
      <div class="ticker">
        <span><strong>SSQ</strong> 红6+蓝1</span>
        <span><strong>DLT</strong> 前5+后2</span>
        <span><strong>MODE</strong> RESEARCH</span>
        <span class="down"><strong>EDGE</strong> UNPROVEN</span>
        <span class="up"><strong>DATA</strong> LOCAL CSV</span>
      </div>
      <div class="conn" :class="connClass">
        <span class="conn-dot" />
        <span>{{ readyText }}</span>
        <span>{{ clock }}</span>
      </div>
    </header>

    <div class="workspace">
      <aside class="rail">
        <div class="rail-label">Workspace</div>
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
        <div class="rail-foot">
          <div>ENDPOINT</div>
          <div>{{ status.baseUrl }}</div>
          <div v-if="status.error" class="err">{{ status.error }}</div>
        </div>
      </aside>

      <main class="content">
        <router-view />
      </main>
    </div>

    <footer class="statusbar">
      <span>LQ · RESEARCH ONLY · NO INVESTMENT ADVICE</span>
      <span>仅供研究娱乐 · 开奖随机 · <em>不构成投注建议</em></span>
    </footer>
  </div>
</template>
