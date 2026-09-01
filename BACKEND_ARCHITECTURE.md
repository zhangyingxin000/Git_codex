# AutoTest AI Backend Architecture

## Current Decision

The backend is now treated as one formal platform backend. `app.py` remains the runnable entry while core business capability moves into `quality_hub_backend/`.

This keeps all existing data and reports available while making the codebase ready for FastAPI, SQLAlchemy, and an enterprise deployment model.

## Runtime Shape

```text
app.py
  HTTP compatibility entry
  static file serving
  current SQLite bootstrap
  routes delegate to quality_hub_backend services

quality_hub_backend/
  schemas/        stable API and domain contracts
  repositories/   platform-owned data access
  services/       business decisions and orchestration
  adapters/       enterprise-recognized tools such as JMeter/Newman/pytest
  security/       credentials, redaction, readonly policies
```

## Data Boundary

```text
Platform local database
  writable
  stores assets, mappings, rules, snapshots, reports, diagnosis
  migration target: MySQL/PostgreSQL

Company MySQL
  readonly
  used for evidence and comparison
  never mutated by the platform

Company Redis
  readonly
  only safe read commands and snapshots
  never SET/DEL/FLUSH/CONFIG
```

## Migration Rule

Existing data is not discarded. The migration path is:

1. Keep SQLite as the development source of truth.
2. Move business logic from `app.py` into `quality_hub_backend/services`.
3. Move SQL access into repositories with stable return models.
4. Add FastAPI routes that call the same services.
5. Replace repository implementation with SQLAlchemy when ready.
6. Export/import platform tables only; never migrate real company MySQL/Redis data.

## First Extracted Capability

`ProjectDiagnosisService` is now the formal source for platform gap diagnosis:

- missing requirements or interface documents
- missing executable cases
- missing test accounts or reusable credentials
- missing MySQL schema or mappings
- missing Redis readonly source or mappings
- missing endpoint-level validation evidence
- failed execution evidence that needs classification
