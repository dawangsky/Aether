import { createRouter, createWebHashHistory } from 'vue-router'
import DrawsView from './views/DrawsView.vue'
import AnalyzeView from './views/AnalyzeView.vue'
import PredictView from './views/PredictView.vue'
import BacktestView from './views/BacktestView.vue'
import CheckView from './views/CheckView.vue'
import TicketView from './views/TicketView.vue'
import ThemeView from './views/ThemeView.vue'

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/draws' },
    { path: '/draws', component: DrawsView, meta: { title: '开奖' } },
    { path: '/analyze', component: AnalyzeView, meta: { title: '分析' } },
    { path: '/predict', component: PredictView, meta: { title: '预测' } },
    { path: '/ticket', component: TicketView, meta: { title: '选号' } },
    { path: '/backtest', component: BacktestView, meta: { title: '回测' } },
    { path: '/check', component: CheckView, meta: { title: '核对' } },
    { path: '/themes', component: ThemeView, meta: { title: '主题' } }
  ]
})
