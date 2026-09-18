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
PYTHONPATH=backend uv run python -m app.cli.index_local ./data/sources
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
`MetadataDocument`.

### Identifiants

L'identifiant est **opaque** : il n'expose ni le nom de la source ni
l'arborescence de celle-ci. La provenance reste lisible dans les champs du
document : `source_name` (la source) et `source_path` (la clé native dans
cette source, p. ex. un chemin relatif à la racine du connecteur).

Il est calculé de façon déterministe par `document_id(source_name,
source_path)` — un SHA-256 tronqué à 32 caractères hexadécimaux. Deux
conséquences utiles :

- ré-indexer une source met à jour les documents existants au lieu de créer
  des doublons ;
- l'identifiant ne dépend pas de l'endroit où la source est montée, donc il
  reste le même d'une machine à l'autre.

Un identifiant contenant un `/` est refusé (`422`) : il doit tenir dans un
seul segment d'URL.

```bash
# id de « notes.md » dans la source « local-files »
ID=$(PYTHONPATH=backend uv run python -c \
  'from app.connectors.base import document_id; print(document_id("local-files", "notes.md"))')

curl -X POST http://localhost:8000/api/documents \
  -H 'Content-Type: application/json' \
  -d "{\"id\": \"$ID\", \"title\": \"Notes\",
       \"source_name\": \"local-files\", \"source_path\": \"notes.md\",
       \"format\": \"markdown\"}"

curl -X PATCH "http://localhost:8000/api/documents/$ID" \
  -H 'Content-Type: application/json' \
  -d '{"title": "Notes v2"}'

curl -X DELETE "http://localhost:8000/api/documents/$ID"
```

Ces routes écrivent directement dans Typesense avec la clé d'administration du
backend : elles ne sont pas authentifiées et ne doivent pas être exposées en
l'état hors du poste de développement.

### Enrichissements et ré-indexation

Un document a deux propriétaires. Les champs **dérivés** appartiennent à la
source : le connecteur les réécrit à chaque passe. Les champs **enrichis** ont
été écrits via l'API : ils appartiennent à l'utilisateur et la ré-indexation ne
les touche plus.

La frontière n'est pas une liste figée, elle est constatée : tout champ écrit
par un `PATCH` ou un `PUT` est ajouté à `enriched_fields` sur le document. La
règle tient en une phrase — *ce que l'API écrit, l'indexation ne le réécrit
pas*.

```text
PATCH {"description": "Compte rendu du 12/03"}
  └─> enriched_fields = ["description"]

puis ré-indexation de la source
  └─> title, content, updated_at… réécrits depuis le fichier
      description      conservée
```

Côté code, trois écritures distinctes, et une seule à utiliser depuis un
connecteur :

| Méthode | Appelant | Effet |
| --- | --- | --- |
| `TypesenseService.index()` | CLI, connecteurs | réécrit la source, préserve `enriched_fields` |
| `TypesenseService.replace()` | `PUT /api/documents/{id}` | remplace et marque les champs fournis |
| `TypesenseService.update()` | `PATCH /api/documents/{id}` | modifie et marque les champs touchés |

`enriched_fields` est un champ système : une valeur envoyée par un client ou un
connecteur est ignorée, seul le service la calcule.

L'ingestion appelle `TypesenseService` en direct, sans passer par l'API HTTP :
en local, la sérialisation et l'aller-retour réseau n'apporteraient rien. Le
point d'entrée unique est le service, pas le transport.

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
