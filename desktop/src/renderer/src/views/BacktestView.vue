<script setup lang="ts">
import { computed, ref } from 'vue'
import { api, type GameKey } from '../api/client'

const game = ref<GameKey>('ssq')
const windowSize = ref(30)
const n = ref(5)
const periods = ref(40)
const seed = ref(42)
const loading = ref(false)
const error = ref('')
const payload = ref<any>(null)

const edgeDelta = computed(() => {
  if (!payload.value) return null
  const m = payload.value.result.model_avg_best_main
  const r = payload.value.result.rand_avg_best_main
  return Number((m - r).toFixed(3))
})

async function run() {
  loading.value = true
  error.value = ''
  try {
    payload.value = await api.backtest({
      game: game.value,
      window: windowSize.value,
      n: n.value,
      periods: periods.value,
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
        <h1>回测台</h1>
        <p class="lead">策略 vs 随机基线 · 检验是否存在统计 Edge</p>
      </div>
      <div class="panel-id">BACKTEST</div>
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
        Window
        <input v-model.number="windowSize" type="number" min="10" max="100" />
      </label>
      <label class="field">
        每期注数
        <input v-model.number="n" type="number" min="1" max="10" />
      </label>
      <label class="field">
        回测期数
        <input v-model.number="periods" type="number" min="10" max="200" />
      </label>
      <button class="btn" :disabled="loading" @click="run">运行回测</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="payload">
      <div class="metric-row">
        <div class="metric">
          <div class="label">策略最佳命中</div>
          <div class="value flat">{{ payload.result.model_avg_best_main }}</div>
        </div>
        <div class="metric">
          <div class="label">随机最佳命中</div>
          <div class="value">{{ payload.result.rand_avg_best_main }}</div>
        </div>
        <div class="metric">
          <div class="label">Δ Edge</div>
          <div
            class="value"
            :class="edgeDelta !== null && edgeDelta > 0 ? 'bid' : edgeDelta !== null && edgeDelta < 0 ? 'ask' : 'flat'"
          >
            {{ edgeDelta === null ? '—' : (edgeDelta > 0 ? '+' : '') + edgeDelta }}
          </div>
        </div>
        <div class="metric">
          <div class="label">命中≥3 期数</div>
          <div class="value">{{ payload.result.model_ge3 }} / {{ payload.result.rand_ge3 }}</div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-hd">
          <span>绩效对比</span>
          <span>{{ payload.result.periods }} 期</span>
        </div>
        <div class="panel-bd" style="padding: 0">
          <table class="data">
            <thead>
              <tr>
                <th>指标</th>
                <th class="num">策略 Model</th>
                <th class="num">随机 Random</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>主号最佳命中均值</td>
                <td class="num">{{ payload.result.model_avg_best_main }}</td>
                <td class="num">{{ payload.result.rand_avg_best_main }}</td>
              </tr>
              <tr>
                <td>主号平均命中</td>
                <td class="num">{{ payload.result.model_avg_main }}</td>
                <td class="num">{{ payload.result.rand_avg_main }}</td>
              </tr>
              <tr>
                <td>特码最佳命中均值</td>
                <td class="num">{{ payload.result.model_avg_best_special }}</td>
                <td class="num">{{ payload.result.rand_avg_best_special }}</td>
              </tr>
              <tr>
                <td>主号≥3 期数</td>
                <td class="num">{{ payload.result.model_ge3 }}</td>
                <td class="num">{{ payload.result.rand_ge3 }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-hd"><span>逐期明细</span><span>RECENT</span></div>
        <div class="panel-bd" style="padding: 0">
          <table class="data">
            <thead>
              <tr>
                <th>期号</th>
                <th>开奖</th>
                <th class="num">策略主</th>
                <th class="num">策略特</th>
                <th class="num">随机主</th>
                <th class="num">随机特</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in payload.result.details" :key="row[0]">
                <td>{{ row[0] }}</td>
                <td>{{ row[1] }}</td>
                <td class="num">{{ row[2] }}</td>
                <td class="num">{{ row[3] }}</td>
                <td class="num">{{ row[4] }}</td>
                <td class="num">{{ row[5] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="note">{{ payload.note }}</div>
    </template>
  </section>
</template>
