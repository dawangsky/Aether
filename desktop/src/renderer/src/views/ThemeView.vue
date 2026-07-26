<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { THEMES, applyTheme, loadTheme, type ThemeId } from '../themes'

const current = ref<ThemeId>(loadTheme())

function select(id: ThemeId) {
  current.value = id
  applyTheme(id)
}

onMounted(() => {
  applyTheme(current.value)
})
</script>

<template>
  <section class="page">
    <div class="page-head">
      <div>
        <h1>界面主题</h1>
        <p class="lead">共 4 套风格，点选即时切换整站；选定后本地记住</p>
      </div>
      <div class="panel-id">THEME</div>
    </div>

    <div class="theme-grid">
      <button
        v-for="t in THEMES"
        :key="t.id"
        type="button"
        class="theme-card"
        :class="{ active: current === t.id }"
        @click="select(t.id)"
      >
        <div class="theme-card-top">
          <div>
            <div class="theme-name">{{ t.name }}</div>
            <div class="theme-tag">{{ t.tagline }}</div>
          </div>
          <div class="theme-badge" v-if="current === t.id">使用中</div>
        </div>
        <p class="theme-vibe">{{ t.vibe }}</p>
        <div class="theme-swatches">
          <span v-for="(c, i) in t.swatches" :key="i" :style="{ background: c }" />
        </div>
        <div class="theme-mini" :data-preview="t.id">
          <div class="mini-bar" />
          <div class="mini-body">
            <div class="mini-rail" />
            <div class="mini-main">
              <div class="mini-line" />
              <div class="mini-line short" />
              <div class="mini-chips">
                <i /><i /><i />
              </div>
            </div>
          </div>
        </div>
      </button>
    </div>

    <div class="note">
      当前：<strong>{{ THEMES.find((x) => x.id === current)?.name }}</strong>。
      告诉我你选哪一套，我可以把它定为默认并收掉其它备选。
    </div>
  </section>
</template>
