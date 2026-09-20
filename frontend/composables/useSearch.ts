export interface SearchHit {
  document: {
    id: string
    title: string
    description?: string
    summary?: string
    content?: string
    source_name?: string
    source_type?: string
    format?: string
    language?: string
    access?: string
    created_at?: string | number
    updated_at?: string | number
    tags?: string[]
    source_uri?: string
    metadata?: Record<string, unknown>
  }
  highlights?: Record<string, { matched_tokens?: string[]; snippet?: string }>
}

export interface SearchResponse {
  found: number
  page: number
  hits: SearchHit[]
  facet_counts?: Array<{ field_name: string; counts: Array<{ value: string; count: number }> }>
}

export type SortField = 'relevance' | 'title' | 'updated_at' | 'source_name' | 'format'
export type SortOrder = 'asc' | 'desc'

export function useSearch() {
  const config = useRuntimeConfig()
  const query = ref('')
  const documentFormat = ref('all')
  const sortBy = ref<SortField>('relevance')
  const sortOrder = ref<SortOrder>('asc')
  const pending = ref(false)
  const error = ref<string | null>(null)
  const result = ref<SearchResponse | null>(null)

  async function search() {
    pending.value = true
    error.value = null
    try {
      result.value = await $fetch<SearchResponse>('/search', {
        baseURL: config.public.apiBase,
        query: {
          q: query.value,
          ...(documentFormat.value !== 'all' ? { format: documentFormat.value } : {}),
          ...(sortBy.value !== 'relevance'
            ? { sort_by: sortBy.value, sort_order: sortOrder.value }
            : {})
        }
      })
    } catch {
      error.value = "L'API de recherche est indisponible."
    } finally {
      pending.value = false
    }
  }

  return { query, documentFormat, sortBy, sortOrder, pending, error, result, search }
}
