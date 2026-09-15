export interface SearchHit {
  document: {
    id: string
    title: string
    description?: string
    content?: string
    source_name?: string
    source_type?: string
    format?: string
    tags?: string[]
    source_uri?: string
  }
  highlights?: Record<string, { matched_tokens?: string[]; snippet?: string }>
}

export interface SearchResponse {
  found: number
  page: number
  hits: SearchHit[]
  facet_counts?: Array<{ field_name: string; counts: Array<{ value: string; count: number }> }>
}

export function useSearch() {
  const config = useRuntimeConfig()
  const query = ref('')
  const pending = ref(false)
  const error = ref<string | null>(null)
  const result = ref<SearchResponse | null>(null)

  async function search() {
    pending.value = true
    error.value = null
    try {
      result.value = await $fetch<SearchResponse>('/search', {
        baseURL: config.public.apiBase,
        query: { q: query.value }
      })
    } catch {
      error.value = "L'API de recherche est indisponible."
    } finally {
      pending.value = false
    }
  }

  return { query, pending, error, result, search }
}
