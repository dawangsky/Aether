import { createRouter, createWebHashHistory } from 'vue-router'
import DrawsView from './views/DrawsView.vue'
import AnalyzeView from './views/AnalyzeView.vue'
import PredictView from './views/PredictView.vue'
import BacktestView from './views/BacktestView.vue'

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/draws' },
    { path: '/draws', component: DrawsView, meta: { title: '开奖' } },
    { path: '/analyze', component: AnalyzeView, meta: { title: '分析' } },
    { path: '/predict', component: PredictView, meta: { title: '预测' } },
    { path: '/backtest', component: BacktestView, meta: { title: '回测' } }
  ]
})
