<script setup lang="ts">
import { ref } from 'vue'
import { api, type GameKey } from '../api/client'

const game = ref<GameKey>('ssq')
const n = ref(2)
const windowSize = ref(50)
const seed = ref<number | null>(42)
const loading = ref(false)
const error = ref('')
const result = ref<any>(null)

async function run() {
  loading.value = true
  error.value = ''
  try {
    result.value = await api.predict({
      game: game.value,
      n: n.value,
      window: windowSize.value,
      seed: seed.value
    })
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page">
    <div class="page-head">
      <div>
        <h1>信号生成</h1>
        <p class="lead">约束采样 · 形态校验 · 仅供研究参考</p>
      </div>
      <div class="panel-id">SIGNAL</div>
    </div>

    <div class="toolbar">
      <label class="field">
        彩种
        <select v-model="game">
          <option value="ssq">SSQ 双色球</option>
          <option value="dlt">DLT 大乐透</option>
        </select>
      </label>
      <label class="field">
        注数
        <input v-model.number="n" type="number" min="1" max="10" />
      </label>
      <label class="field">
        Window
        <input v-model.number="windowSize" type="number" min="10" max="200" />
      </label>
      <label class="field">
        Seed
        <input v-model.number="seed" type="number" />
      </label>
      <button class="btn" :disabled="loading" @click="run">生成信号</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="result">
      <div class="metric-row">
        <div class="metric">
          <div class="label">Window</div>
          <div class="value">{{ result.window }}</div>
        </div>
        <div class="metric">
          <div class="label">参考期号</div>
          <div class="value flat">{{ result.last_issue }}</div>
        </div>
        <div class="metric">
          <div class="label">信号注数</div>
          <div class="value">{{ result.tickets.length }}</div>
        </div>
        <div class="metric">
          <div class="label">Edge</div>
          <div class="value ask">N/A</div>
        </div>
      </div>

      <div class="panel" v-for="(t, idx) in result.tickets" :key="idx">
        <div class="panel-hd">
          <span>信号单 {{ String(idx + 1).padStart(2, '0') }}</span>
          <span>SUM {{ t.meta.sum }}</span>
        </div>
        <div class="panel-bd">
          <div class="balls" style="margin-bottom: 10px">
            <span v-for="num in t.main" :key="'m' + num" class="ball main">{{
              String(num).padStart(2, '0')
            }}</span>
            <span v-for="num in t.special" :key="'s' + num" class="ball special">{{
              String(num).padStart(2, '0')
            }}</span>
          </div>
          <div class="kv">
            <div class="k">奇偶</div>
            <div class="v">{{ t.meta.odd_even }}</div>
            <div class="k">大小</div>
            <div class="v">{{ t.meta.big_small }}</div>
            <div class="k">三区</div>
            <div class="v">{{ t.meta.zones }}</div>
            <div class="k">遗漏层</div>
            <div class="v">{{ t.meta.bands }}</div>
          </div>
        </div>
      </div>

      <div class="note">{{ result.disclaimer }}</div>
    </template>
  </section>
</template>
