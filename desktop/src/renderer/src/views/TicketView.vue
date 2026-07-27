<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { api, type GameKey } from '../api/client'

type Source = 'recommend' | 'manual'
type BetMode = 'single' | 'compound'

const game = ref<GameKey>('ssq')
const source = ref<Source>('recommend')
const betMode = ref<BetMode>('single')
const mainCount = ref(7)
const specialCount = ref(1)
const windowSize = ref(50)

const selectedMain = ref<number[]>([])
const selectedSpecial = ref<number[]>([])
const loading = ref(false)
const error = ref('')
const plan = ref<any>(null)

const mainMax = computed(() => (game.value === 'ssq' ? 33 : 35))
const specialMax = computed(() => (game.value === 'ssq' ? 16 : 12))
const mainNeed = computed(() => (game.value === 'ssq' ? 6 : 5))
const specialNeed = computed(() => (game.value === 'ssq' ? 1 : 2))
const mainLabel = computed(() => (game.value === 'ssq' ? '红球' : '前区'))
const specialLabel = computed(() => (game.value === 'ssq' ? '蓝球' : '后区'))

const mainNums = computed(() => Array.from({ length: mainMax.value }, (_, i) => i + 1))
const specialNums = computed(() => Array.from({ length: specialMax.value }, (_, i) => i + 1))
const mainCols = computed(() => Math.ceil(mainMax.value / 3))
const specialCols = computed(() => Math.ceil(specialMax.value / 2))

const compoundPresets = computed(() =>
  game.value === 'ssq'
    ? [
        { label: '7+1', m: 7, s: 1 },
        { label: '8+1', m: 8, s: 1 },
        { label: '6+2', m: 6, s: 2 },
        { label: '7+2', m: 7, s: 2 }
      ]
    : [
        { label: '6+2', m: 6, s: 2 },
        { label: '7+2', m: 7, s: 2 },
        { label: '6+3', m: 6, s: 3 },
        { label: '5+3', m: 5, s: 3 }
      ]
)

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function comb(n: number, k: number): number {
  if (k < 0 || n < 0 || k > n) return 0
  if (k === 0 || k === n) return 1
  let r = 1
  for (let i = 1; i <= k; i++) r = (r * (n - k + i)) / i
  return Math.round(r)
}

function quoteFromCounts(m: number, s: number) {
  if (m < mainNeed.value || s < specialNeed.value) {
    return { bets: 0, cost: 0, formula: `${m}+${s}`, mode: '选号中' as string }
  }
  const bets = comb(m, mainNeed.value) * comb(s, specialNeed.value)
  const mode =
    m === mainNeed.value && s === specialNeed.value ? '单式' : '复式'
  return {
    bets,
    cost: bets * 2,
    formula: `${m}+${s}`,
    mode,
    unit: `C(${m},${mainNeed.value})×C(${s},${specialNeed.value})`
  }
}

const targetMainCount = computed(() =>
  betMode.value === 'single' ? mainNeed.value : mainCount.value
)
const targetSpecialCount = computed(() =>
  betMode.value === 'single' ? specialNeed.value : specialCount.value
)

const liveQuote = computed(() => {
  const m = selectedMain.value.length
  const s = selectedSpecial.value.length
  if (m >= mainNeed.value && s >= specialNeed.value) {
    return quoteFromCounts(m, s)
  }
  if (source.value === 'manual') {
    return quoteFromCounts(m, s)
  }
  return quoteFromCounts(targetMainCount.value, targetSpecialCount.value)
})

const canRecommend = computed(() => {
  if (betMode.value === 'single') return true
  return (
    mainCount.value >= mainNeed.value &&
    mainCount.value <= mainMax.value &&
    specialCount.value >= specialNeed.value &&
    specialCount.value <= specialMax.value
  )
})

const canQuoteManual = computed(
  () =>
    selectedMain.value.length >= mainNeed.value &&
    selectedSpecial.value.length >= specialNeed.value
)

function resetDefaults() {
  mainCount.value = mainNeed.value + 1
  specialCount.value = specialNeed.value
  selectedMain.value = []
  selectedSpecial.value = []
  plan.value = null
  error.value = ''
}

function applyPreset(m: number, s: number) {
  betMode.value = 'compound'
  mainCount.value = m
  specialCount.value = s
  plan.value = null
}

function toggleMain(n: number) {
  const set = new Set(selectedMain.value)
  if (set.has(n)) set.delete(n)
  else set.add(n)
  selectedMain.value = [...set].sort((a, b) => a - b)
  plan.value = null
}

function toggleSpecial(n: number) {
  const set = new Set(selectedSpecial.value)
  if (set.has(n)) set.delete(n)
  else set.add(n)
  selectedSpecial.value = [...set].sort((a, b) => a - b)
  plan.value = null
}

function clearMain() {
  selectedMain.value = []
  plan.value = null
}

function clearSpecial() {
  selectedSpecial.value = []
  plan.value = null
}

function clearAll() {
  clearMain()
  clearSpecial()
}

async function generateRecommend() {
  if (!canRecommend.value) {
    error.value = `复式条件需在 ${mainNeed.value}–${mainMax.value}+${specialNeed.value}–${specialMax.value} 范围内`
    return
  }
  loading.value = true
  error.value = ''
  plan.value = null
  try {
    const data = await api.ticketPlan({
      game: game.value,
      mode: betMode.value,
      main_count: betMode.value === 'compound' ? mainCount.value : null,
      special_count: betMode.value === 'compound' ? specialCount.value : null,
      window: windowSize.value
    })
    plan.value = data
    selectedMain.value = [...data.main]
    selectedSpecial.value = [...data.special]
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function quoteManual() {
  if (!canQuoteManual.value) {
    error.value = `请至少选择 ${mainNeed.value} 个${mainLabel.value}、${specialNeed.value} 个${specialLabel.value}`
    return
  }
  loading.value = true
  error.value = ''
  try {
    plan.value = await api.ticketQuote({
      game: game.value,
      main: selectedMain.value,
      special: selectedSpecial.value
    })
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

watch(game, resetDefaults)
watch(betMode, () => {
  if (betMode.value === 'single') {
    mainCount.value = mainNeed.value
    specialCount.value = specialNeed.value
  } else if (mainCount.value <= mainNeed.value && specialCount.value <= specialNeed.value) {
    mainCount.value = mainNeed.value + 1
    specialCount.value = specialNeed.value
  }
  plan.value = null
})
watch(source, () => {
  plan.value = null
  error.value = ''
})
</script>

<template>
  <section class="page">
    <div class="page-head">
      <div>
        <h1>下一期选号</h1>
        <p class="lead">按专家形态因子加权分层配号 · 单式 / 复式 · 实时估算费用</p>
      </div>
      <div class="panel-id">TICKET</div>
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
        来源
        <select v-model="source">
          <option value="recommend">智能推荐</option>
          <option value="manual">手选</option>
        </select>
      </label>
      <label class="field">
        形态
        <select v-model="betMode" :disabled="source === 'manual'">
          <option value="single">单式 {{ mainNeed }}+{{ specialNeed }}</option>
          <option value="compound">复式</option>
        </select>
      </label>
      <template v-if="source === 'recommend' && betMode === 'compound'">
        <label class="field">
          {{ mainLabel }}个数
          <input v-model.number="mainCount" type="number" :min="mainNeed" :max="mainMax" />
        </label>
        <label class="field">
          {{ specialLabel }}个数
          <input
            v-model.number="specialCount"
            type="number"
            :min="specialNeed"
            :max="specialMax"
          />
        </label>
      </template>
      <template v-if="source === 'recommend'">
        <label class="field">
          Window
          <input v-model.number="windowSize" type="number" min="10" max="200" />
        </label>
        <button class="btn" :disabled="loading || !canRecommend" @click="generateRecommend">
          生成推荐
        </button>
      </template>
      <template v-else>
        <button class="btn secondary" @click="clearAll">清空选号</button>
        <button class="btn" :disabled="loading || !canQuoteManual" @click="quoteManual">
          计算费用
        </button>
      </template>
    </div>

    <div v-if="source === 'recommend' && betMode === 'compound'" class="toolbar" style="margin-top: -4px">
      <span class="muted" style="align-self: center">快捷复式</span>
      <button
        v-for="p in compoundPresets"
        :key="p.label"
        class="btn secondary"
        type="button"
        @click="applyPreset(p.m, p.s)"
      >
        {{ p.label }}
      </button>
    </div>

    <div class="metric-row">
      <div class="metric">
        <div class="label">投注公式</div>
        <div class="value flat">{{ liveQuote.formula }}</div>
      </div>
      <div class="metric">
        <div class="label">形态</div>
        <div class="value">{{ liveQuote.mode }}</div>
      </div>
      <div class="metric">
        <div class="label">注数</div>
        <div class="value">{{ liveQuote.bets }}</div>
      </div>
      <div class="metric">
        <div class="label">费用（2元/注）</div>
        <div class="value bid">{{ liveQuote.cost }} 元</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-hd">
        <span
          >{{ mainLabel }}（{{
            source === 'manual' ? '点击手选' : '生成后可微调，也可直接手选'
          }}）</span
        >
        <button class="btn secondary" style="height: 24px; padding: 0 8px" @click="clearMain">
          清空
        </button>
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
        <span>{{ specialLabel }}</span>
        <button class="btn secondary" style="height: 24px; padding: 0 8px" @click="clearSpecial">
          清空
        </button>
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

    <template v-if="plan">
      <div class="panel">
        <div class="panel-hd">
          <span>方案明细</span>
          <span>{{ plan.mode === 'single' ? '单式' : '复式' }} · {{ plan.formula }}</span>
        </div>
        <div class="panel-bd">
          <div class="balls" style="margin-bottom: 12px">
            <span v-for="n in plan.main" :key="'pm' + n" class="ball main">{{ pad(n) }}</span>
            <span v-for="n in plan.special" :key="'ps' + n" class="ball special">{{ pad(n) }}</span>
          </div>
          <div class="kv">
            <div class="k">号码</div>
            <div class="v">{{ plan.formatted }}</div>
            <div class="k">推荐方式</div>
            <div class="v">
              {{ plan.strategy?.label || '专家形态加权 + 分层配号' }}（{{ plan.method }}）
            </div>
            <div class="k" v-if="plan.strategy?.notes?.length">因子</div>
            <div class="v" v-if="plan.strategy?.notes?.length">
              {{ plan.strategy.notes.join(' · ') }}
            </div>
            <div class="k">拆注公式</div>
            <div class="v">{{ plan.unit_bets }} = {{ plan.bets }} 注</div>
            <div class="k">费用</div>
            <div class="v">{{ plan.cost }} 元（{{ plan.price_per_bet }} 元/注）</div>
            <div class="k" v-if="plan.last_issue">参考期号</div>
            <div class="v" v-if="plan.last_issue">{{ plan.last_issue }}</div>
            <div class="k" v-if="plan.main_scores">主区得分</div>
            <div class="v" v-if="plan.main_scores">
              {{
                Object.entries(plan.main_scores)
                  .map(([n, s]) => `${String(n).padStart(2, '0')}(${s})`)
                  .join(' ')
              }}
            </div>
            <div class="k" v-if="plan.special_scores">特区得分</div>
            <div class="v" v-if="plan.special_scores">
              {{
                Object.entries(plan.special_scores)
                  .map(([n, s]) => `${String(n).padStart(2, '0')}(${s})`)
                  .join(' ')
              }}
            </div>
          </div>
        </div>
      </div>
      <div class="note">
        策略融合常见专家维度：多窗冷热、遗漏回补、重号邻号、空区/012 路、热温冷分层配号。同一窗口数据下结果确定。
        仅供研究娱乐，开奖近乎随机，不构成投注建议。单式为标准 {{ mainNeed }}+{{ specialNeed }}；复式按组合数计费。
      </div>
    </template>
  </section>
</template>
