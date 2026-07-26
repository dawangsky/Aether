<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, type GameKey } from '../api/client'

type IssueOption = { issue: string; date: string; formatted: string }

const game = ref<GameKey>('ssq')
const issue = ref('')
const issues = ref<IssueOption[]>([])
const loadingIssues = ref(false)
const selectedMain = ref<number[]>([])
const selectedSpecial = ref<number[]>([])
const loading = ref(false)
const error = ref('')
const result = ref<any>(null)

const mainMax = computed(() => (game.value === 'ssq' ? 33 : 35))
const specialMax = computed(() => (game.value === 'ssq' ? 16 : 12))
const mainNeed = computed(() => (game.value === 'ssq' ? 6 : 5))
const specialNeed = computed(() => (game.value === 'ssq' ? 1 : 2))

const mainNums = computed(() => Array.from({ length: mainMax.value }, (_, i) => i + 1))
const specialNums = computed(() => Array.from({ length: specialMax.value }, (_, i) => i + 1))

/** 红球/前区均分 3 行；蓝球/后区均分 2 行 */
const mainCols = computed(() => Math.ceil(mainMax.value / 3))
const specialCols = computed(() => Math.ceil(specialMax.value / 2))

const mainLabel = computed(() => (game.value === 'ssq' ? '红球' : '前区'))
const specialLabel = computed(() => (game.value === 'ssq' ? '蓝球' : '后区'))

const selectedDraw = computed(() => issues.value.find((x) => x.issue === issue.value) || null)

const canSubmit = computed(
  () =>
    !!issue.value &&
    selectedMain.value.length >= mainNeed.value &&
    selectedSpecial.value.length >= specialNeed.value
)

const modeHint = computed(() => {
  const m = selectedMain.value.length
  const s = selectedSpecial.value.length
  if (m === mainNeed.value && s === specialNeed.value) return '单式'
  if (m > mainNeed.value || s > specialNeed.value) return '复式'
  return '选号中'
})

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function formatMoney(n: number | null | undefined) {
  if (n == null || Number.isNaN(n)) return '—'
  return `${Number(n).toLocaleString('zh-CN')} 元`
}

function toggleMain(n: number) {
  const set = new Set(selectedMain.value)
  if (set.has(n)) set.delete(n)
  else set.add(n)
  selectedMain.value = [...set].sort((a, b) => a - b)
  result.value = null
}

function toggleSpecial(n: number) {
  const set = new Set(selectedSpecial.value)
  if (set.has(n)) set.delete(n)
  else set.add(n)
  selectedSpecial.value = [...set].sort((a, b) => a - b)
  result.value = null
}

function clearMain() {
  selectedMain.value = []
  result.value = null
}

function clearSpecial() {
  selectedSpecial.value = []
  result.value = null
}

function clearAll() {
  clearMain()
  clearSpecial()
}

async function loadIssues(preferLatest = true) {
  loadingIssues.value = true
  error.value = ''
  try {
    const data = await api.draws(game.value, 100)
    const opts = [...data.items]
      .reverse()
      .map((x) => ({
        issue: String(x.issue),
        date: String(x.date),
        formatted: String(x.formatted)
      }))
    issues.value = opts
    if (!opts.length) {
      issue.value = ''
      error.value = '本地暂无开奖期号，请先在「开奖行情」同步数据'
      return
    }
    if (preferLatest || !opts.some((x) => x.issue === issue.value)) {
      issue.value = opts[0].issue
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loadingIssues.value = false
  }
}

async function syncAndReload() {
  loadingIssues.value = true
  error.value = ''
  try {
    await api.update(game.value)
    await loadIssues(true)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
    loadingIssues.value = false
  }
}

function parseDrawNumbers(formatted: string): { main: number[]; special: number[] } {
  const [mainPart = '', specialPart = ''] = formatted.split('+').map((s) => s.trim())
  const toNums = (text: string) =>
    text
      .split(/[\s,，、|+/]+/)
      .filter(Boolean)
      .map((x) => Number(x))
      .filter((n) => Number.isFinite(n))
  return { main: toNums(mainPart), special: toNums(specialPart) }
}

function fillExample(kind: 'single' | 'compound') {
  const draw = selectedDraw.value?.formatted
  if (!draw) {
    error.value = '请先加载并选择期号'
    return
  }
  const parsed = parseDrawNumbers(draw)
  if (kind === 'single') {
    selectedMain.value = [...parsed.main].sort((a, b) => a - b)
    selectedSpecial.value = [...parsed.special].sort((a, b) => a - b)
  } else if (game.value === 'ssq') {
    const extraMain = [1, 5].filter((n) => !parsed.main.includes(n))
    const extraBlue = [5].filter((n) => !parsed.special.includes(n))
    selectedMain.value = [...parsed.main, ...extraMain].sort((a, b) => a - b)
    selectedSpecial.value = [...parsed.special, ...extraBlue].sort((a, b) => a - b)
  } else {
    const extraMain = [1].filter((n) => !parsed.main.includes(n))
    const extraBack = [2].filter((n) => !parsed.special.includes(n))
    selectedMain.value = [...parsed.main, ...extraMain].sort((a, b) => a - b)
    selectedSpecial.value = [...parsed.special, ...extraBack].sort((a, b) => a - b)
  }
  result.value = null
}

async function run() {
  if (!canSubmit.value) {
    error.value = `请至少选择 ${mainNeed.value} 个${mainLabel.value}、${specialNeed.value} 个${specialLabel.value}`
    return
  }
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await api.check({
      game: game.value,
      issue: issue.value,
      main: selectedMain.value,
      special: selectedSpecial.value
    })
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

watch(game, () => {
  result.value = null
  clearAll()
  void loadIssues(true)
})

onMounted(() => {
  void loadIssues(true)
})
</script>

<template>
  <section class="page">
    <div class="page-head">
      <div>
        <h1>中奖核对</h1>
        <p class="lead">点击号码选号 · 支持单式 / 复式</p>
      </div>
      <div class="panel-id">CHECK</div>
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
        期号
        <select v-model="issue" :disabled="loadingIssues || !issues.length" style="min-width: 220px">
          <option v-if="!issues.length" value="" disabled>暂无期号</option>
          <option v-for="item in issues" :key="item.issue" :value="item.issue">
            {{ item.issue }}（{{ item.date }}）
          </option>
        </select>
      </label>
      <button class="btn secondary" :disabled="loadingIssues" @click="loadIssues(false)">刷新期号</button>
      <button class="btn secondary" :disabled="loadingIssues" @click="syncAndReload">同步最新</button>
      <button class="btn secondary" :disabled="!issue" @click="fillExample('single')">单式示例</button>
      <button class="btn secondary" :disabled="!issue" @click="fillExample('compound')">复式示例</button>
      <button class="btn secondary" @click="clearAll">清空选号</button>
      <button class="btn" :disabled="loading || !canSubmit" @click="run">核对</button>
    </div>

    <p v-if="selectedDraw" class="muted">当前开奖：{{ selectedDraw.formatted }}</p>

    <div class="metric-row">
      <div class="metric">
        <div class="label">已选{{ mainLabel }}</div>
        <div class="value flat">{{ selectedMain.length }}</div>
      </div>
      <div class="metric">
        <div class="label">已选{{ specialLabel }}</div>
        <div class="value flat">{{ selectedSpecial.length }}</div>
      </div>
      <div class="metric">
        <div class="label">投注形态</div>
        <div class="value">{{ modeHint }}</div>
      </div>
      <div class="metric">
        <div class="label">最少要求</div>
        <div class="value" style="font-size: 14px">{{ mainNeed }}+{{ specialNeed }}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-hd">
        <span>{{ mainLabel }}（点击选择，≥{{ mainNeed }}）</span>
        <button class="btn secondary" style="height: 24px; padding: 0 8px" @click="clearMain">清空</button>
      </div>
      <div class="panel-bd">
        <div
          class="pick-grid"
          :style="{ gridTemplateColumns: `repeat(${mainCols}, minmax(0, 1fr))` }"
        >
          <button
            v-for="n in mainNums"
            :key="'m' + n"
            type="button"
            class="pick-num main"
            :class="{ on: selectedMain.includes(n) }"
            @click="toggleMain(n)"
          >
            {{ pad(n) }}
          </button>
        </div>
        <div class="balls pick-selected" v-if="selectedMain.length">
          <span v-for="n in selectedMain" :key="'sm' + n" class="ball main">{{ pad(n) }}</span>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-hd">
        <span>{{ specialLabel }}（点击选择，≥{{ specialNeed }}）</span>
        <button class="btn secondary" style="height: 24px; padding: 0 8px" @click="clearSpecial">清空</button>
      </div>
      <div class="panel-bd">
        <div
          class="pick-grid"
          :style="{ gridTemplateColumns: `repeat(${specialCols}, minmax(0, 1fr))` }"
        >
          <button
            v-for="n in specialNums"
            :key="'s' + n"
            type="button"
            class="pick-num special"
            :class="{ on: selectedSpecial.includes(n) }"
            @click="toggleSpecial(n)"
          >
            {{ pad(n) }}
          </button>
        </div>
        <div class="balls pick-selected" v-if="selectedSpecial.length">
          <span v-for="n in selectedSpecial" :key="'ss' + n" class="ball special">{{ pad(n) }}</span>
        </div>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="result">
      <div class="metric-row">
        <div class="metric">
          <div class="label">模式</div>
          <div class="value flat">{{ result.mode === 'single' ? '单式' : '复式' }}</div>
        </div>
        <div class="metric">
          <div class="label">总注数</div>
          <div class="value">{{ result.total_bets }}</div>
        </div>
        <div class="metric">
          <div class="label">中奖注数</div>
          <div class="value" :class="result.won ? 'bid' : 'ask'">{{ result.winning_bets }}</div>
        </div>
        <div class="metric">
          <div class="label">最高奖等</div>
          <div class="value" :class="result.won ? 'bid' : 'ask'">{{ result.prize_name }}</div>
        </div>
        <div class="metric">
          <div class="label">奖金合计</div>
          <div class="value" :class="result.won ? 'bid' : 'ask'">
            {{ formatMoney(result.total_prize) }}
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-hd">
          <span>对照结果</span>
          <span>{{ result.issue }}</span>
        </div>
        <div class="panel-bd">
          <div class="kv">
            <div class="k">开奖日期</div>
            <div class="v">{{ result.draw_date }}</div>
            <div class="k">开奖号码</div>
            <div class="v">{{ result.draw_formatted }}</div>
            <div class="k">投注号码</div>
            <div class="v">{{ result.ticket_formatted }}</div>
            <div class="k">命中池</div>
            <div class="v">
              主区 {{ result.main_hit }}/{{ result.main_selected }} · 特区
              {{ result.special_hit }}/{{ result.special_selected }}
            </div>
            <div class="k">说明</div>
            <div class="v">{{ result.rule }}</div>
          </div>
        </div>
      </div>

      <div class="panel" v-if="result.levels?.length">
        <div class="panel-hd"><span>分奖等明细</span><span>官网单注奖金 × 注数</span></div>
        <div class="panel-bd" style="padding: 0">
          <table class="data">
            <thead>
              <tr>
                <th>奖等 / 规则</th>
                <th class="num">单注奖金</th>
                <th class="num">注数</th>
                <th class="num">中奖奖金</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lv in result.levels" :key="lv.prize_level + lv.rule">
                <td>{{ lv.prize_name }} {{ lv.rule }}</td>
                <td class="num">{{ formatMoney(lv.unit_prize) }}</td>
                <td class="num">{{ lv.count }}</td>
                <td class="num">{{ formatMoney(lv.amount) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="note">
        复式按官方拆解为单式组合计数；单注奖金取自官网当期公告（点「同步最新」可刷新）。
        规则形如 6+1 / 2+1，表示主区命中 + 特区命中。大乐透自 2026014 期起按新 7 奖级计。
      </div>
    </template>
  </section>
</template>
