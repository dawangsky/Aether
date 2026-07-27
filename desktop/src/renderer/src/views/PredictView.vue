<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, type GameKey } from '../api/client'

type IssueOption = { issue: string; date: string }

const game = ref<GameKey>('ssq')
const n = ref(2)
const windowSize = ref(50)
const seed = ref<number | null>(42)
const asOfIssue = ref('')
const issues = ref<IssueOption[]>([])
const loadingIssues = ref(false)
const loading = ref(false)
const error = ref('')
const result = ref<any>(null)

const hasTargetDraw = computed(
  () => !!(result.value?.target_issue && result.value?.checks?.length)
)

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function formatMoney(n: number | null | undefined) {
  if (n == null || Number.isNaN(n)) return '—'
  return `${Number(n).toLocaleString('zh-CN')} 元`
}

async function loadIssues(preferLatest = true) {
  loadingIssues.value = true
  error.value = ''
  try {
    const data = await api.draws(game.value, 500)
    const opts = [...data.items]
      .reverse()
      .map((x) => ({
        issue: String(x.issue),
        date: String(x.date)
      }))
    issues.value = opts
    if (!opts.length) {
      asOfIssue.value = ''
      error.value = '本地暂无开奖期号，请先在「开奖行情」同步数据'
      return
    }
    if (preferLatest || !opts.some((x) => x.issue === asOfIssue.value)) {
      asOfIssue.value = opts[0].issue
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loadingIssues.value = false
  }
}

async function run() {
  if (!asOfIssue.value) {
    error.value = '请选择参考期号'
    return
  }
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await api.predict({
      game: game.value,
      n: n.value,
      window: windowSize.value,
      seed: seed.value,
      as_of_issue: asOfIssue.value
    })
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

watch(game, () => {
  result.value = null
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
        <h1>信号生成</h1>
        <p class="lead">可选历史期号回看 · 若下一期已开奖则自动对照核对</p>
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
        参考期号
        <select
          v-model="asOfIssue"
          :disabled="loadingIssues || !issues.length"
          style="min-width: 220px"
        >
          <option v-if="!issues.length" value="" disabled>暂无期号</option>
          <option v-for="item in issues" :key="item.issue" :value="item.issue">
            {{ item.issue }}（{{ item.date }}）
          </option>
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
      <button class="btn secondary" :disabled="loadingIssues" @click="loadIssues(false)">
        刷新期号
      </button>
      <button class="btn" :disabled="loading || !asOfIssue" @click="run">生成信号</button>
    </div>

    <p class="muted">
      参考期号为历史截止点；信号对应「下一期」。若下一期号码已在本地，将在每张信号单下方显示中奖对照。
    </p>

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
          <div class="label">对照期号</div>
          <div class="value flat">{{ result.target_issue || '尚未开奖' }}</div>
        </div>
        <div class="metric">
          <div class="label">信号注数</div>
          <div class="value">{{ result.tickets.length }}</div>
        </div>
      </div>

      <p v-if="hasTargetDraw" class="muted">
        对照开奖 {{ result.target_issue }}（{{ result.target_draw_date }}）：{{
          result.target_draw_formatted
        }}
      </p>
      <p v-else-if="result.target_issue == null" class="muted">
        参考期之后尚无开奖数据，无法做中奖对照（通常选最新期时如此）。
      </p>

      <div class="panel" v-for="(t, idx) in result.tickets" :key="idx">
        <div class="panel-hd">
          <span>信号单 {{ String(idx + 1).padStart(2, '0') }}</span>
          <span v-if="result.checks?.[idx]" :class="result.checks[idx].won ? 'bid' : 'ask'">
            {{ result.checks[idx].won ? result.checks[idx].prize_name : '未中奖' }}
          </span>
          <span v-else>SUM {{ t.meta.sum }}</span>
        </div>
        <div class="panel-bd">
          <div class="balls" style="margin-bottom: 10px">
            <span v-for="num in t.main" :key="'m' + num" class="ball main">{{ pad(num) }}</span>
            <span v-for="num in t.special" :key="'s' + num" class="ball special">{{
              pad(num)
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

          <template v-if="result.checks?.[idx]">
            <div class="check-block">
              <div class="check-block__title">中奖对照 · {{ result.checks[idx].issue }}</div>
              <div class="kv">
                <div class="k">开奖号码</div>
                <div class="v">{{ result.checks[idx].draw_formatted }}</div>
                <div class="k">投注号码</div>
                <div class="v">{{ result.checks[idx].ticket_formatted }}</div>
                <div class="k">模式 / 注数</div>
                <div class="v">
                  {{ result.checks[idx].mode === 'single' ? '单式' : '复式' }} ·
                  {{ result.checks[idx].total_bets }} 注 · 中
                  {{ result.checks[idx].winning_bets }} 注
                </div>
                <div class="k">命中池</div>
                <div class="v">
                  主区 {{ result.checks[idx].main_hit }}/{{ result.checks[idx].main_selected }} ·
                  特区 {{ result.checks[idx].special_hit }}/{{
                    result.checks[idx].special_selected
                  }}
                </div>
                <div class="k">奖金</div>
                <div class="v">
                  {{ formatMoney(result.checks[idx].total_prize) }} ·
                  {{ result.checks[idx].rule }}
                </div>
              </div>
              <table
                v-if="result.checks[idx].levels?.length"
                class="data"
                style="margin-top: 12px"
              >
                <thead>
                  <tr>
                    <th>奖等 / 规则</th>
                    <th class="num">单注奖金</th>
                    <th class="num">注数</th>
                    <th class="num">中奖奖金</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="lv in result.checks[idx].levels"
                    :key="lv.prize_level + lv.rule"
                  >
                    <td>{{ lv.prize_name }} {{ lv.rule }}</td>
                    <td class="num">{{ formatMoney(lv.unit_prize) }}</td>
                    <td class="num">{{ lv.count }}</td>
                    <td class="num">{{ formatMoney(lv.amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>
      </div>

      <div class="note">{{ result.disclaimer }}</div>
    </template>
  </section>
</template>

<style scoped>
.check-block {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--line);
}

.check-block__title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-dim);
  margin-bottom: 8px;
  letter-spacing: 0.04em;
}
</style>
