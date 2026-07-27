<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, type GameKey } from '../api/client'

type IssueOption = { issue: string; date: string; formatted: string }
type TicketDraft = { id: number; main: number[]; special: number[] }
type TicketResult = { index: number; ok: boolean; error?: string; data?: any }

let ticketSeq = 1
function emptyTicket(): TicketDraft {
  return { id: ticketSeq++, main: [], special: [] }
}

const game = ref<GameKey>('ssq')
const issue = ref('')
const issues = ref<IssueOption[]>([])
const loadingIssues = ref(false)
const tickets = ref<TicketDraft[]>([emptyTicket()])
const loading = ref(false)
const error = ref('')
const results = ref<TicketResult[] | null>(null)

const mainMax = computed(() => (game.value === 'ssq' ? 33 : 35))
const specialMax = computed(() => (game.value === 'ssq' ? 16 : 12))
const mainNeed = computed(() => (game.value === 'ssq' ? 6 : 5))
const specialNeed = computed(() => (game.value === 'ssq' ? 1 : 2))
const mainNums = computed(() => Array.from({ length: mainMax.value }, (_, i) => i + 1))
const specialNums = computed(() => Array.from({ length: specialMax.value }, (_, i) => i + 1))
const mainCols = computed(() => Math.ceil(mainMax.value / 3))
const specialCols = computed(() => Math.ceil(specialMax.value / 2))
const mainLabel = computed(() => (game.value === 'ssq' ? '红球' : '前区'))
const specialLabel = computed(() => (game.value === 'ssq' ? '蓝球' : '后区'))
const selectedDraw = computed(() => issues.value.find((x) => x.issue === issue.value) || null)

const readyTickets = computed(() =>
  tickets.value.filter(
    (t) => t.main.length >= mainNeed.value && t.special.length >= specialNeed.value
  )
)

const canSubmit = computed(() => !!issue.value && readyTickets.value.length > 0)

const summary = computed(() => {
  if (!results.value?.length) return null
  const ok = results.value.filter((r) => r.ok && r.data)
  const won = ok.filter((r) => r.data.won)
  const totalBets = ok.reduce((s, r) => s + (r.data.total_bets || 0), 0)
  const winningBets = ok.reduce((s, r) => s + (r.data.winning_bets || 0), 0)
  const prizes = ok.map((r) => r.data.total_prize as number | null)
  const totalPrize = prizes.every((p) => p != null)
    ? prizes.reduce((s, p) => s + (p || 0), 0)
    : null
  return {
    groups: results.value.length,
    ok: ok.length,
    won: won.length,
    totalBets,
    winningBets,
    totalPrize
  }
})

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function formatMoney(n: number | null | undefined) {
  if (n == null || Number.isNaN(n)) return '—'
  return `${Number(n).toLocaleString('zh-CN')} 元`
}

function modeOf(t: TicketDraft) {
  const m = t.main.length
  const s = t.special.length
  if (m === mainNeed.value && s === specialNeed.value) return '单式'
  if (m >= mainNeed.value && s >= specialNeed.value) return '复式'
  return '选号中'
}

function toggleMain(ti: number, n: number) {
  const t = tickets.value[ti]
  const set = new Set(t.main)
  if (set.has(n)) set.delete(n)
  else set.add(n)
  t.main = [...set].sort((a, b) => a - b)
  results.value = null
}

function toggleSpecial(ti: number, n: number) {
  const t = tickets.value[ti]
  const set = new Set(t.special)
  if (set.has(n)) set.delete(n)
  else set.add(n)
  t.special = [...set].sort((a, b) => a - b)
  results.value = null
}

function clearTicket(ti: number) {
  tickets.value[ti].main = []
  tickets.value[ti].special = []
  results.value = null
}

function addTicketAfter(ti: number) {
  tickets.value.splice(ti + 1, 0, emptyTicket())
  results.value = null
}

function removeTicket(ti: number) {
  if (tickets.value.length <= 1) {
    clearTicket(0)
    return
  }
  tickets.value.splice(ti, 1)
  results.value = null
}

function clearAll() {
  tickets.value = [emptyTicket()]
  results.value = null
  error.value = ''
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
  const t = tickets.value[0] || emptyTicket()
  if (!tickets.value.length) tickets.value = [t]
  if (kind === 'single') {
    t.main = [...parsed.main].sort((a, b) => a - b)
    t.special = [...parsed.special].sort((a, b) => a - b)
  } else if (game.value === 'ssq') {
    const extraMain = [1, 5].filter((n) => !parsed.main.includes(n))
    const extraBlue = [5].filter((n) => !parsed.special.includes(n))
    t.main = [...parsed.main, ...extraMain].sort((a, b) => a - b)
    t.special = [...parsed.special, ...extraBlue].sort((a, b) => a - b)
  } else {
    const extraMain = [1].filter((n) => !parsed.main.includes(n))
    const extraBack = [2].filter((n) => !parsed.special.includes(n))
    t.main = [...parsed.main, ...extraMain].sort((a, b) => a - b)
    t.special = [...parsed.special, ...extraBack].sort((a, b) => a - b)
  }
  results.value = null
}

async function run() {
  if (!issue.value) {
    error.value = '请选择期号'
    return
  }
  const ready = readyTickets.value
  if (!ready.length) {
    error.value = `请至少完整填写一组：${mainNeed.value} 个${mainLabel.value}、${specialNeed.value} 个${specialLabel.value}`
    return
  }
  loading.value = true
  error.value = ''
  results.value = null
  try {
    const out: TicketResult[] = []
    for (let i = 0; i < tickets.value.length; i++) {
      const t = tickets.value[i]
      if (t.main.length < mainNeed.value || t.special.length < specialNeed.value) {
        out.push({ index: i + 1, ok: false, error: '选号未完成，已跳过' })
        continue
      }
      try {
        const data = await api.check({
          game: game.value,
          issue: issue.value,
          main: t.main,
          special: t.special
        })
        out.push({ index: i + 1, ok: true, data })
      } catch (e) {
        out.push({
          index: i + 1,
          ok: false,
          error: e instanceof Error ? e.message : String(e)
        })
      }
    }
    results.value = out
    if (out.every((r) => !r.ok)) {
      error.value = out.find((r) => r.error)?.error || '核对失败'
    }
  } finally {
    loading.value = false
  }
}

watch(game, () => {
  results.value = null
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
        <p class="lead">支持多组号码 · 单式 / 复式 · 组后可继续加一组</p>
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
      <button class="btn secondary" @click="clearAll">清空全部</button>
      <button class="btn" :disabled="loading || !canSubmit" @click="run">
        核对（{{ readyTickets.length }} 组）
      </button>
    </div>

    <p v-if="selectedDraw" class="muted">当前开奖：{{ selectedDraw.formatted }}</p>

    <div v-for="(t, ti) in tickets" :key="t.id" class="ticket-block">
      <div class="metric-row">
        <div class="metric">
          <div class="label">第 {{ ti + 1 }} 组</div>
          <div class="value flat">{{ modeOf(t) }}</div>
        </div>
        <div class="metric">
          <div class="label">已选{{ mainLabel }}</div>
          <div class="value flat">{{ t.main.length }}</div>
        </div>
        <div class="metric">
          <div class="label">已选{{ specialLabel }}</div>
          <div class="value flat">{{ t.special.length }}</div>
        </div>
        <div class="metric">
          <div class="label">最少要求</div>
          <div class="value" style="font-size: 14px">{{ mainNeed }}+{{ specialNeed }}</div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-hd">
          <span>{{ mainLabel }}（≥{{ mainNeed }}）</span>
          <button class="btn secondary" style="height: 24px; padding: 0 8px" @click="clearTicket(ti)">
            清空本组
          </button>
        </div>
        <div class="panel-bd">
          <div
            class="pick-grid"
            :style="{ gridTemplateColumns: `repeat(${mainCols}, minmax(0, 1fr))` }"
          >
            <button
              v-for="n in mainNums"
              :key="'m' + t.id + '-' + n"
              type="button"
              class="pick-num main"
              :class="{ on: t.main.includes(n) }"
              @click="toggleMain(ti, n)"
            >
              {{ pad(n) }}
            </button>
          </div>
          <div class="balls pick-selected" v-if="t.main.length">
            <span v-for="n in t.main" :key="'sm' + t.id + '-' + n" class="ball main">{{
              pad(n)
            }}</span>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-hd">
          <span>{{ specialLabel }}（≥{{ specialNeed }}）</span>
        </div>
        <div class="panel-bd">
          <div
            class="pick-grid"
            :style="{ gridTemplateColumns: `repeat(${specialCols}, minmax(0, 1fr))` }"
          >
            <button
              v-for="n in specialNums"
              :key="'s' + t.id + '-' + n"
              type="button"
              class="pick-num special"
              :class="{ on: t.special.includes(n) }"
              @click="toggleSpecial(ti, n)"
            >
              {{ pad(n) }}
            </button>
          </div>
          <div class="balls pick-selected" v-if="t.special.length">
            <span v-for="n in t.special" :key="'ss' + t.id + '-' + n" class="ball special">{{
              pad(n)
            }}</span>
          </div>
        </div>
      </div>

      <div class="ticket-actions">
        <button class="btn" type="button" @click="addTicketAfter(ti)">加一组</button>
        <button
          class="btn secondary"
          type="button"
          :disabled="tickets.length <= 1"
          @click="removeTicket(ti)"
        >
          删除本组
        </button>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="results && summary">
      <div class="metric-row">
        <div class="metric">
          <div class="label">核验组数</div>
          <div class="value">{{ summary.ok }}/{{ summary.groups }}</div>
        </div>
        <div class="metric">
          <div class="label">中奖组数</div>
          <div class="value" :class="summary.won ? 'bid' : 'ask'">{{ summary.won }}</div>
        </div>
        <div class="metric">
          <div class="label">总注数</div>
          <div class="value">{{ summary.totalBets }}</div>
        </div>
        <div class="metric">
          <div class="label">中奖注数</div>
          <div class="value" :class="summary.winningBets ? 'bid' : 'ask'">
            {{ summary.winningBets }}
          </div>
        </div>
        <div class="metric">
          <div class="label">奖金合计</div>
          <div class="value" :class="summary.totalPrize ? 'bid' : 'ask'">
            {{ formatMoney(summary.totalPrize) }}
          </div>
        </div>
      </div>

      <div v-for="r in results" :key="'r' + r.index" class="panel">
        <div class="panel-hd">
          <span>第 {{ r.index }} 组结果</span>
          <span v-if="r.ok && r.data" :class="r.data.won ? 'bid' : 'ask'">
            {{ r.data.won ? r.data.prize_name : '未中奖' }}
          </span>
          <span v-else class="ask">失败</span>
        </div>
        <div class="panel-bd">
          <p v-if="!r.ok" class="error" style="margin: 0">{{ r.error }}</p>
          <template v-else-if="r.data">
            <div class="kv">
              <div class="k">投注号码</div>
              <div class="v">{{ r.data.ticket_formatted }}</div>
              <div class="k">开奖号码</div>
              <div class="v">{{ r.data.draw_formatted }}</div>
              <div class="k">模式 / 注数</div>
              <div class="v">
                {{ r.data.mode === 'single' ? '单式' : '复式' }} · {{ r.data.total_bets }} 注 · 中
                {{ r.data.winning_bets }} 注
              </div>
              <div class="k">命中池</div>
              <div class="v">
                主区 {{ r.data.main_hit }}/{{ r.data.main_selected }} · 特区
                {{ r.data.special_hit }}/{{ r.data.special_selected }}
              </div>
              <div class="k">奖金</div>
              <div class="v">{{ formatMoney(r.data.total_prize) }} · {{ r.data.rule }}</div>
            </div>
            <table v-if="r.data.levels?.length" class="data" style="margin-top: 12px">
              <thead>
                <tr>
                  <th>奖等 / 规则</th>
                  <th class="num">单注奖金</th>
                  <th class="num">注数</th>
                  <th class="num">中奖奖金</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="lv in r.data.levels" :key="lv.prize_level + lv.rule">
                  <td>{{ lv.prize_name }} {{ lv.rule }}</td>
                  <td class="num">{{ formatMoney(lv.unit_prize) }}</td>
                  <td class="num">{{ lv.count }}</td>
                  <td class="num">{{ formatMoney(lv.amount) }}</td>
                </tr>
              </tbody>
            </table>
          </template>
        </div>
      </div>

      <div class="note">
        未完成选号的组会跳过；完整组按官方规则逐组核对后汇总。复式按组合拆注计费/计奖。
      </div>
    </template>
  </section>
</template>

<style scoped>
.ticket-block {
  margin-bottom: 18px;
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--line);
}

.ticket-block:last-of-type {
  border-bottom: none;
}

.ticket-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 4px 0 8px;
}
</style>
