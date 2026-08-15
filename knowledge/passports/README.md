# Artifact passport registry

This directory is the durable index of research artifacts and experiment runs.

- `schema.json` — machine-readable required fields.
- Run passports are generated next to reports by `run-controls`.
- Accepted milestone evidence may be copied into `evidence/runs/<RUN-ID>/`.

The passport is an index and interpretation layer. Large source artifacts remain in
their canonical locations and are linked by path plus SHA-256 instead of being copied.
