# Context

This folder holds repo orientation and workflow context that does not fit cleanly into product or architecture docs.

## Start Here

- [`index.yaml`](index.yaml): compact routing manifest used by later AI-SDLC phases
- [`repo-map.md`](repo-map.md): the quickest durable way to find the source, test, config, and workflow entrypoints that matter
- [`gaps.md`](gaps.md): unresolved questions, weak signals, and stale areas that should not be guessed through
- [`bootstrap-report.md`](bootstrap-report.md): the evidence trail and review notes from the last bootstrap pass

## What Belongs Here

Use `docs/context/` for information such as:

- repo navigation and entrypoints
- workflow or team conventions
- integration notes and operational context
- uncertainty tracking and stale-doc detection
- bootstrap or promotion review evidence that should stay visible

## Context vs Patterns

- `docs/context/`: facts, routing, and uncertainty about the repo, tooling, or team workflow
- `docs/patterns/`: reusable implementation approaches that future work should follow

`bootstrap-report.md` is a snapshot review artifact, not the canonical source of durable repo truth.
If the information answers “what is true about this repo, what should be read first, or what remains unclear,” it usually belongs here.
