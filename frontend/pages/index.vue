<script setup lang="ts">
const { query, pending, error, result, search } = useSearch()

onMounted(search)
</script>

<template>
  <main class="page-shell">
    <header class="hero">
      <p class="eyebrow">DOC CENTRAL</p>
      <h1>Retrouver vos sources, simplement.</h1>
      <p class="intro">
        Une recherche unifiée dans les métadonnées et contenus provenant de vos différentes sources.
      </p>

      <form class="search-form" @submit.prevent="search">
        <input
          v-model="query"
          type="search"
          placeholder="Rechercher un document, une source, un mot-clé…"
          aria-label="Rechercher"
        >
        <button type="submit" :disabled="pending">
          {{ pending ? 'Recherche…' : 'Rechercher' }}
        </button>
      </form>
    </header>

    <section class="results" aria-live="polite">
      <p v-if="error" class="message error">{{ error }}</p>
      <p v-else-if="result" class="result-count">{{ result.found }} résultat(s)</p>
      <p v-if="result && result.hits.length === 0" class="message">Aucun résultat.</p>

      <article v-for="hit in result?.hits" :key="hit.document.id" class="result-card">
        <div class="result-meta">
          <span>{{ hit.document.source_name }}</span>
          <span v-if="hit.document.format">{{ hit.document.format }}</span>
        </div>
        <h2>{{ hit.document.title }}</h2>
        <p>{{ hit.highlights?.content?.snippet || hit.document.description || hit.document.content }}</p>
        <div v-if="hit.document.tags?.length" class="tags">
          <span v-for="tag in hit.document.tags" :key="tag">{{ tag }}</span>
        </div>
      </article>
    </section>
  </main>
</template>
