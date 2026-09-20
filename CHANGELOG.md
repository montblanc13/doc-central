# Changelog

## [0.2.0] - 2026-09-20

### Ajouté

- Ajout d'un connecteur Google Drive en lecture seule avec authentification
  OAuth et commandes dédiées pour créer le jeton et indexer les documents.
- Ajout de résumés sémantiques via OpenAI Responses API ou Anthropic Messages
  API, sélectionnables par configuration.
- Ajout dans l'interface de liens vers les documents sources, de métadonnées
  enrichies et de filtres par format avec tri configurable.

### Modifié

- Enrichissement de la recherche Typesense avec les résumés, les facettes,
  le filtrage par format et le tri sur des champs autorisés.
- Modernisation de l'interface Nuxt avec Nuxt UI, les icônes Lucide et une
  présentation plus compacte des résultats.
