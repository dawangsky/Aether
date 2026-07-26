<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, type GameKey } from '../api/client'

const game = ref<GameKey>('ssq')
const windowSize = ref(50)
const loading = ref(false)
const error = ref('')
const data = ref<any>(null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await api.analyze(game.value, windowSize.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="page">
    <div class="page-head">
      <div>
        <h1>因子分析</h1>
        <p class="lead">冷热分布 · 遗漏分层 · 上期形态复盘</p>
      </div>
      <div class="panel-id">ANALYZE</div>
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
        <input v-model.number="windowSize" type="number" min="10" max="200" />
      </label>
      <button class="btn" :disabled="loading" @click="load">开始分析</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="data">
      <div class="metric-row">
        <div class="metric">
          <div class="label">上期和值</div>
          <div class="value flat">{{ data.last_pattern.sum }}</div>
        </div>
        <div class="metric">
          <div class="label">跨度 Span</div>
          <div class="value">{{ data.last_pattern.span }}</div>
        </div>
        <div class="metric">
          <div class="label">奇偶</div>
          <div class="value">{{ data.last_pattern.odd_even }}</div>
        </div>
        <div class="metric">
          <div class="label">三区</div>
          <div class="value">{{ data.last_pattern.zones }}</div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-hd">
          <span>上期开奖</span>
          <span>{{ data.last_draw.issue }}</span>
        </div>
        <div class="panel-bd">
          <div class="kv">
            <div class="k">日期</div>
            <div class="v">{{ data.last_draw.date }}</div>
            <div class="k">号码</div>
            <div class="v">{{ data.last_draw.formatted }}</div>
            <div class="k">中枢</div>
            <div class="v">
              均值 {{ data.history_summary.sum_mean }} / 中位 {{ data.history_summary.sum_median }}
            </div>
          </div>
        </div>
      </div>

      <div class="grid-2">
        <div class="panel">
          <div class="panel-hd"><span>热号 Hot</span><span>FREQ</span></div>
          <div class="panel-bd" style="padding: 0">
            <table class="data">
              <thead>
                <tr>
                  <th>号码</th>
                  <th class="num">出现次数</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in data.main_hot" :key="'h' + row.number">
                  <td>{{ String(row.number).padStart(2, '0') }}</td>
                  <td class="num">{{ row.count }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="panel">
          <div class="panel-hd"><span>遗漏 Omission</span><span>LAG</span></div>
          <div class="panel-bd" style="padding: 0">
            <table class="data">
              <thead>
                <tr>
                  <th>号码</th>
                  <th class="num">当前</th>
                  <th class="num">均值</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in data.main_omissions" :key="'o' + row.number">
                  <td>{{ String(row.number).padStart(2, '0') }}</td>
                  <td class="num">{{ row.current }}</td>
                  <td class="num">{{ row.average }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-hd"><span>遗漏分层</span><span>BAND</span></div>
        <div class="panel-bd" style="padding: 0">
          <table class="data">
            <thead>
              <tr>
                <th>分层</th>
                <th>号码</th>
                <th class="num">个数</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(nums, name) in data.omission_bands" :key="name">
                <td>{{ name }}</td>
                <td>{{ nums.map((n: number) => String(n).padStart(2, '0')).join(' ') || '—' }}</td>
                <td class="num">{{ nums.length }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="note">{{ data.disclaimer }}</div>
    </template>
  </section>
</template>
