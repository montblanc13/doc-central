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

## API

| Méthode | Chemin | Rôle |
| --- | --- | --- |
| `GET` | `/api/health` | Sonde de disponibilité |
| `GET` | `/api/search` | Recherche plein texte (`q`, `page`, `per_page`) |
| `POST` | `/api/documents` | Crée un document (`409` si l'`id` existe déjà) |
| `GET` | `/api/documents/{id}` | Lit un document |
| `PUT` | `/api/documents/{id}` | Remplace un document (upsert) |
| `PATCH` | `/api/documents/{id}` | Met à jour les champs fournis uniquement |
| `DELETE` | `/api/documents/{id}` | Supprime un document (`204`) |

Le corps des requêtes `POST` et `PUT` suit le contrat canonique
`MetadataDocument`. L'identifiant peut contenir des `/` (les identifiants
produits par les connecteurs ont la forme `source:/chemin/absolu`) : il est
donc lu comme un chemin complet et doit être encodé dans l'URL.

```bash
curl -X POST http://localhost:8000/api/documents \
  -H 'Content-Type: application/json' \
  -d '{"id": "local-files:/data/notes.md", "title": "Notes", "format": "markdown"}'

curl -X PATCH 'http://localhost:8000/api/documents/local-files:/data/notes.md' \
  -H 'Content-Type: application/json' \
  -d '{"title": "Notes v2"}'

curl -X DELETE 'http://localhost:8000/api/documents/local-files:/data/notes.md'
```

Ces routes écrivent directement dans Typesense avec la clé d'administration du
backend : elles ne sont pas authentifiées et ne doivent pas être exposées en
l'état hors du poste de développement.

## Tests

```bash
uv run pytest
uv run ruff check .
```

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
