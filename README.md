# Doc Central

Moteur de recherche de métadonnées provenant de sources hétérogènes.

Le projet combine :

- un backend Python/FastAPI géré avec UV ;
- Typesense pour l'indexation et la recherche ;
- un frontend Nuxt 4 ;
- des connecteurs extensibles qui produisent un format de métadonnées commun.

## Démarrage rapide

### 1. Lancer Typesense

```bash
docker compose up -d typesense typesense-dashboard
```

Le dashboard Typesense est disponible sur <http://localhost:8180>. Il permet
de consulter les collections, inspecter les documents et tester les recherches.
Il s'agit d'un outil d'administration de développement : la clé configurée
dans `infra/typesense-dashboard/config.json` est volontairement la clé locale
`xyz` et doit être remplacée ou protégée avant toute exposition réseau.

### 2. Installer le backend

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload --app-dir backend
```

L'API est disponible sur <http://localhost:8000> et sa documentation sur
<http://localhost:8000/docs>.

### 3. Lancer Nuxt

```bash
cd frontend
npm install
npm run dev
```

L'interface est disponible sur <http://localhost:3000>.

## Rechercher et filtrer

L'interface permet de rechercher dans les titres, contenus, résumés et
métadonnées indexés. Chaque résultat expose sa source, son format, sa date de
modification et, lorsque disponible, un lien vers le document original.

La barre de filtres permet de sélectionner un format et de trier les résultats
par pertinence, titre, date de modification, source ou format, dans l'ordre
croissant ou décroissant. L'API accepte ces mêmes options sur `GET /api/search`
avec les paramètres `format`, `sort_by` et `sort_order`.

## Indexer un dossier local

```bash
PYTHONPATH=backend uv run python -m app.cli.index_local ./data/sources
```

Les formats texte, Markdown, JSON et CSV sont pris en charge par le premier
connecteur. Les fichiers de métadonnées générés sont écrits dans
`data/metadata/` au format JSONL.

## Indexer Google Drive

Créer un client OAuth de type « application de bureau » dans Google Cloud,
activer l'API Google Drive, puis enregistrer le fichier téléchargé sous
`secrets/google-drive/credentials.json`. Le premier lancement ouvre le
navigateur pour obtenir un jeton en lecture seule, conservé dans
`data/google-drive-token.json`.

Créer d'abord le jeton OAuth, sans lancer l'indexation :

```bash
PYTHONPATH=backend uv run python -m app.cli.auth_drive
```

Puis lancer la synchronisation :

```bash
PYTHONPATH=backend uv run python -m app.cli.index_drive
```

Les Google Docs, Sheets et Slides sont exportés en texte lorsque Google le
permet. Les autres fichiers sont indexés avec leurs métadonnées Drive. Pour
limiter le périmètre à un dossier, définir `GOOGLE_DRIVE_FOLDER_ID` dans `.env`.

Un résumé sémantique est généré pour chaque document contenant du texte. Le
fournisseur est sélectionnable avec `AI_PROVIDER` (`openai`, `anthropic` ou
`none`). Par défaut, l'implémentation OpenAI utilise `OPENAI_API_KEY` et
`OPENAI_MODEL=gpt-5-mini` ; pour Anthropic, définir `AI_PROVIDER=anthropic`,
`ANTHROPIC_API_KEY` et `ANTHROPIC_MODEL=claude-sonnet-4-6` (ou un modèle
Claude compatible).

## Architecture

```text
backend/
  app/
    api/             API FastAPI
    cli/             commandes d'ingestion
    connectors/      connecteurs de sources
    models/          contrat canonique de métadonnées
    services/        indexation Typesense
frontend/            application Nuxt 4
infra/               configuration d'infrastructure
```

Le frontend ne communique jamais directement avec la clé d'administration
Typesense : les recherches passent par l'API backend.
