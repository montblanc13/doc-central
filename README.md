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

## Indexer un dossier local

```bash
uv run python -m app.cli.index_local ./data/sources
```

Les formats texte, Markdown, JSON et CSV sont pris en charge par le premier
connecteur. Les fichiers de métadonnées générés sont écrits dans
`data/metadata/` au format JSONL.

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
