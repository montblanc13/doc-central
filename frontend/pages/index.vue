<script setup lang="ts">
import type { SortField, SortOrder } from '~/composables/useSearch'

const { query, documentFormat, sortBy, sortOrder, pending, error, result, search } = useSearch()

const formatOptions = computed(() => [
  { label: 'Tous les formats', value: 'all' },
  ...(result.value?.facet_counts?.find((facet) => facet.field_name === 'format')?.counts ?? [])
    .map((facet) => ({ label: `${facet.value} (${facet.count})`, value: facet.value }))
])

const sortFieldOptions: Array<{ label: string; value: SortField }> = [
  { label: 'Pertinence', value: 'relevance' },
  { label: 'Titre', value: 'title' },
  { label: 'Date de modification', value: 'updated_at' },
  { label: 'Source', value: 'source_name' },
  { label: 'Format', value: 'format' }
]

const sortOrderOptions: Array<{ label: string; value: SortOrder }> = [
  { label: 'Croissant (A → Z)', value: 'asc' },
  { label: 'Décroissant (Z → A)', value: 'desc' }
]

function formatDate(value?: string | number) {
  if (value === undefined || value === null || value === '') return ''

  const numericValue = typeof value === 'number' ? value : Number(value)
  const date = Number.isFinite(numericValue) && numericValue > 0
    ? new Date(numericValue < 10_000_000_000 ? numericValue * 1000 : numericValue)
    : new Date(value)

  if (Number.isNaN(date.getTime())) return ''

  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  }).format(date)
}

onMounted(search)
</script>

<template>
  <main class="page-shell">
    <header class="hero">
      <div class="brand-line">
        <NuxtImg src="/doc-central-mark.svg" alt="" width="48" height="48" class="brand-mark" />
        <p class="eyebrow">DOC CENTRAL</p>
      </div>
      <h1>Retrouver vos sources, simplement.</h1>
      <p class="intro">
        Une recherche unifiée dans les métadonnées et contenus provenant de vos différentes sources.
      </p>

      <form class="search-form" @submit.prevent="search">
        <UInput
          v-model="query"
          type="search"
          size="lg"
          class="search-input"
          placeholder="Rechercher un document, une source, un mot-clé…"
          aria-label="Rechercher"
        >
          <template #leading>
            <Icon name="lucide:search" size="20" />
          </template>
        </UInput>
        <UButton type="submit" size="lg" :loading="pending">
          <Icon name="lucide:search" size="20" />
          {{ pending ? 'Recherche…' : 'Rechercher' }}
        </UButton>
      </form>
    </header>

    <section class="filters" aria-label="Filtres et tri">
      <USelect
        v-model="documentFormat"
        :items="formatOptions"
        value-key="value"
        aria-label="Filtrer par format"
        @update:model-value="search"
      />
      <USelect
        v-model="sortBy"
        :items="sortFieldOptions"
        value-key="value"
        aria-label="Trier par"
        @update:model-value="search"
      />
      <USelect
        v-model="sortOrder"
        :items="sortOrderOptions"
        value-key="value"
        aria-label="Ordre du tri"
        :disabled="sortBy === 'relevance'"
        @update:model-value="search"
      />
    </section>

    <section class="results" aria-live="polite">
      <p v-if="error" class="message error">{{ error }}</p>
      <p v-else-if="result" class="result-count">
        {{ result.found }} résultat(s)
        <span v-if="query.trim()">pour « {{ query.trim() }} »</span>
        <span v-else>dans tous les documents</span>
      </p>
      <p v-if="result && result.hits.length === 0" class="message">Aucun résultat.</p>

      <UCard v-for="hit in result?.hits" :key="hit.document.id" class="result-card">
        <h2>{{ hit.document.title }}</h2>
        <div class="record-metadata" aria-label="Métadonnées du document">
          <span v-if="hit.document.source_name">
            <Icon name="lucide:database" size="15" />
            {{ hit.document.source_name }}
          </span>
          <span v-if="hit.document.format">
            <Icon name="lucide:file-type" size="15" />
            {{ hit.document.format }}
          </span>
          <span v-if="hit.document.language">
            <Icon name="lucide:languages" size="15" />
            {{ hit.document.language }}
          </span>
          <span v-if="formatDate(hit.document.updated_at)">
            <Icon name="lucide:clock-3" size="15" />
            Modifié le {{ formatDate(hit.document.updated_at) }}
          </span>
          <a
            v-if="hit.document.source_uri"
            :href="hit.document.source_uri"
            target="_blank"
            rel="noopener noreferrer"
            class="record-link"
          >
            <Icon name="lucide:external-link" size="15" />
            Ouvrir le document
          </a>
        </div>
        <p>{{ hit.highlights?.summary?.snippet || hit.document.summary || hit.highlights?.content?.snippet || hit.document.description || hit.document.content }}</p>
        <div v-if="hit.document.tags?.length" class="tags">
          <span v-for="tag in hit.document.tags" :key="tag">{{ tag }}</span>
        </div>
      </UCard>
    </section>
  </main>
</template>
