<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'

const links = [
  { to: '/', label: '配置与抓取' },
  { to: '/results', label: '结果' },
  { to: '/predict', label: '分数预测' },
  { to: '/history', label: '历史与续传' },
]
</script>

<template>
  <div class="app-shell">
    <header class="top-nav">
      <div class="nav-inner">
        <RouterLink to="/" class="wordmark">
          <span class="spike" aria-hidden="true">✳</span>
          <span class="wordmark-text">分数择校</span>
        </RouterLink>
        <nav class="nav-links">
          <RouterLink
            v-for="l in links"
            :key="l.to"
            :to="l.to"
            custom
            v-slot="{ navigate, isExactActive }"
          >
            <a class="nav-link" :class="{ active: isExactActive }" :href="l.to" @click.prevent="navigate">{{ l.label }}</a>
          </RouterLink>
        </nav>
      </div>
    </header>

    <main class="main-container">
      <RouterView />
    </main>

    <footer class="site-footer">
      <span class="spike" aria-hidden="true">✳</span>
      <span>score_to_school · 数据来源 掌上高考</span>
    </footer>
  </div>
</template>

<style scoped>
.app-shell { min-height: 100vh; display: flex; flex-direction: column; }

.top-nav {
  height: 64px;
  background: var(--c-canvas);
  border-bottom: 1px solid var(--c-hairline);
  position: sticky; top: 0; z-index: 50;
}
.nav-inner {
  max-width: 1200px; margin: 0 auto; height: 100%;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
}
.wordmark { display: flex; align-items: center; gap: 10px; text-decoration: none; }
.wordmark:hover { text-decoration: none; }
.spike { color: var(--c-ink); font-size: 22px; line-height: 1; }
.wordmark-text {
  font-family: 'Cormorant Garamond', 'Noto Serif SC', serif;
  font-size: 24px; font-weight: 500; color: var(--c-ink); letter-spacing: -0.3px;
}
.nav-links { display: flex; align-items: center; gap: 28px; }
.nav-link {
  font-size: 14px; font-weight: 500; color: var(--c-muted);
  text-decoration: none; padding: 8px 0; position: relative; transition: color .15s;
}
.nav-link:hover { color: var(--c-ink); text-decoration: none; }
.nav-link.active { color: var(--c-ink); }
.nav-link.active::after {
  content: ''; position: absolute; left: 0; right: 0; bottom: -21px;
  height: 2px; background: var(--c-primary);
}

.main-container { flex: 1; max-width: 1200px; margin: 0 auto; width: 100%; padding: 48px 24px 96px; }

.site-footer {
  background: var(--c-surface-dark); color: var(--c-on-dark-soft);
  padding: 32px 24px; font-size: 13px;
  display: flex; align-items: center; gap: 10px; justify-content: center;
}
.site-footer .spike { color: var(--c-on-dark); }

@media (max-width: 640px) {
  .nav-links { gap: 16px; }
  .nav-link { font-size: 13px; }
  .wordmark-text { font-size: 20px; }
}
</style>
