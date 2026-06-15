import { createRouter, createWebHistory } from 'vue-router'
import ConfigScrapeView from '../views/ConfigScrapeView.vue'
import ResultsView from '../views/ResultsView.vue'
import PredictView from '../views/PredictView.vue'
import HistoryView from '../views/HistoryView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'config', component: ConfigScrapeView },
    { path: '/results', name: 'results', component: ResultsView },
    { path: '/predict', name: 'predict', component: PredictView },
    { path: '/history', name: 'history', component: HistoryView },
  ],
})

export default router
