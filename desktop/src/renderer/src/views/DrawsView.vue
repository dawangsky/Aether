<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, type GameKey } from '../api/client'

const game = ref<GameKey>('ssq')
const limit = ref(15)
const loading = ref(false)
const error = ref('')
const total = ref(0)
const items = ref<Array<{ issue: string; date: string; main: number[]; special: number[]; formatted: string }>>([])
const updateMsg = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await api.draws(game.value, limit.value)
    total.value = data.total
    items.value = [...data.items].reverse()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function refreshData() {
  loading.value = true
  error.value = ''
  updateMsg.value = ''
  try {
    const res = await api.update(game.value)
    updateMsg.value = res.results.map((r) => `${r.game}: 共 ${r.total} 期 / 新增 ${r.added}`).join('  ·  ')
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="page">
    <div class="page-head">
      <div>
        <h1>开奖行情</h1>
        <p class="lead">本地历史序列 · 可增量同步官方数据源</p>
      </div>
      <div class="panel-id">DRAWS</div>
    </div>

    <div class="toolbar">
      <label class="field">
        彩种
        <select v-model="game" @change="load">
          <option value="ssq">SSQ 双色球</option>
          <option value="dlt">DLT 大乐透</option>
        </select>
      </label>
      <label class="field">
        最近期数
        <input v-model.number="limit" type="number" min="5" max="100" />
      </label>
      <button class="btn secondary" :disabled="loading" @click="load">刷新</button>
      <button class="btn" :disabled="loading" @click="refreshData">同步数据</button>
    </div>

    <div class="metric-row">
      <div class="metric">
        <div class="label">本地存量</div>
        <div class="value flat">{{ total }}</div>
      </div>
      <div class="metric">
        <div class="label">当前展示</div>
        <div class="value">{{ items.length }}</div>
      </div>
      <div class="metric">
        <div class="label">Instrument</div>
        <div class="value">{{ game.toUpperCase() }}</div>
      </div>
      <div class="metric">
        <div class="label">状态</div>
        <div class="value" :class="loading ? 'flat' : 'bid'">{{ loading ? 'LOAD' : 'IDLE' }}</div>
      </div>
    </div>

    <p v-if="updateMsg" class="muted">{{ updateMsg }}</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="panel">
      <div class="panel-hd">
        <span>开奖明细</span>
        <span>{{ game.toUpperCase() }}</span>
      </div>
      <div class="panel-bd" style="padding: 0">
        <table class="data">
          <thead>
            <tr>
              <th>期号</th>
              <th>日期</th>
              <th>号码</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in items" :key="row.issue">
              <td>{{ row.issue }}</td>
              <td>{{ row.date }}</td>
              <td>
                <div class="balls">
                  <span v-for="n in row.main" :key="'m' + n" class="ball main">{{
                    String(n).padStart(2, '0')
                  }}</span>
                  <span v-for="n in row.special" :key="'s' + n" class="ball special">{{
                    String(n).padStart(2, '0')
                  }}</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>
