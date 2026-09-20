# Instructions pour les agents

## Langue et commandes

- Échanger exclusivement en français.
- Charger systématiquement `/home/slandeau/.codex/RTK.md` avant toute action.
- Préfixer chaque commande shell par `rtk` afin de réduire le bruit de sortie.
- Préserver les changements existants et ne pas utiliser de commande destructive
  sans demande explicite.

## Projet

Doc Central est un moteur de recherche de documents provenant de sources
hétérogènes :

- `backend/` contient l’API FastAPI, les connecteurs et l’indexation Typesense ;
- `frontend/` contient l’application Nuxt 4 ;
- `data/` contient les données locales générées et ne doit pas être versionné ;
- `secrets/` contient les identifiants locaux et ne doit jamais être versionné.

## Stack technique

- **Backend** : Python 3.12+, FastAPI, Uvicorn, Pydantic Settings et UV ;
- **Indexation et recherche** : Typesense 30+, via le client Python ;
- **Sources** : fichiers locaux et Google Drive API v3 avec OAuth 2.0 ;
- **Résumé sémantique** : interface `AIService`, implémentations OpenAI
  Responses API et Anthropic Messages API ;
- **Frontend** : Nuxt 4, Vue 3, TypeScript, Nuxt UI, Nuxt Icon et Nuxt Image ;
- **Infrastructure locale** : Docker Compose pour Typesense et son dashboard ;
- **Tests et qualité** : pytest et Ruff.

### Frontend

- **Nuxt** : 4.5.2, dernière version vérifiée le 20 septembre 2026 ;
- **UI** : Nuxt UI 4.11.1 avec Tailwind CSS 4, éviter de faire des composants custom ;
- **Icônes** : `@nuxt/icon` 2.5.1 avec la collection Lucide ;
- **Images** : `@nuxt/image` 2.1.0 ;
- **Conventions** : privilégier `UButton`, `UInput`, `UCard`, `UBadge`,
  `Icon` et `NuxtImg` lorsque le besoin est couvert ;
- **Validation** : exécuter `npm run build` et `npm run typecheck` depuis
  `frontend/` après toute modification frontend.

### Backend

- **Runtime** : Python `>=3.12` et UV ;
- **API** : FastAPI `>=0.115,<1.0`, Uvicorn et `python-multipart` ;
- **Configuration et modèles** : Pydantic Settings `>=2.7,<3.0` ;
- **Recherche** : client Python Typesense `>=1.1,<2.0` ;
- **Google Drive** : `google-api-python-client` et `google-auth-oauthlib` ;
- **LLM** : SDK OpenAI `>=1.100,<2.0` et Anthropic `>=0.60,<1.0`, derrière
  l’interface `AIService` ;
- **Développement** : pytest, HTTPX et Ruff.

## Validation

Depuis la racine du dépôt :

```bash
rtk uv run pytest -q
rtk uv run ruff check .
```

Pour les commandes Python applicatives, le package est sous `backend/` :

```bash
PYTHONPATH=backend uv run python -m app.cli.index_drive
```

## Indexation Google Drive

- Utiliser OAuth en lecture seule avec un client Google de type « Desktop app ».
- Stocker les identifiants dans `secrets/google-drive/credentials.json`.
- Créer le jeton séparément avec `app.cli.auth_drive` avant la synchronisation.
- Ne jamais afficher ni committer de clé API, jeton OAuth ou fichier de secrets.
- Les résumés sémantiques passent par l’interface `AIService` ; les fournisseurs
  disponibles sont OpenAI et Anthropic.

## Modifications

- Utiliser `apply_patch` pour éditer les fichiers.
- Ajouter ou mettre à jour les tests pour toute nouvelle fonctionnalité.
- Mettre à jour `README.md`, `.env.example` et `uv.lock` lorsque la configuration
  ou les dépendances changent.
