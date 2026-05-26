# Repo Map

Use this file to orient humans and agents quickly.

Capture the highest-signal entrypoints in this repository, not a full file tree dump.

## How to Use This File

- Start with the files that define product behavior or the main runtime flow.
- Include the tests that best explain expected behavior.
- Include the config, manifests, CI, and scripts that shape build, verification, and release behavior.
- Add one short note for why each path matters.
- Prefer repo-specific paths over broad directories whenever possible.

## Read Order

When future work needs fast orientation, the usual order is:

1. core runtime entrypoints
2. highest-signal tests
3. manifests and workflow files
4. durable docs and ADRs that are already repo-specific

Do not list untouched sample files here unless the team has explicitly adapted them for this repo.

## Key Entry Points

| Path | Why it matters |
|---|---|
| `src/...` | Replace with the main runtime or feature entrypoints |
| `tests/...` or `__tests__/...` | Replace with the highest-signal behavior checks |
| `package.json`, `pyproject.toml`, etc. | Replace with the main build or dependency manifest |
| `.github/workflows/...` | Replace with the important CI/CD workflow files |

## Supporting Paths

Use this section for high-value secondary paths such as:

- generated artifacts that matter
- shared utilities
- framework or integration configuration
- durable docs that future work should read early

## Notes

- Prefer the files future feature work should read first.
- Do not mirror a full directory tree.
- Remove this starter text once the repo-specific map is in place.
