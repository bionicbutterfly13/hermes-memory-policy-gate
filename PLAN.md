# Hermes Memory Policy Gate — Local Project Plan

Author: Mani Saint-Victor, MD / bionicbutterfly13
Lane: Hermes/Archimedes memory hygiene plugin
Status: local scaffold + shadow-mode MVP only

## Source of truth

- Local project root: `/Volumes/Asylum/dev/hermes-memory-policy-gate`
- Hermes plugin contract verified from local Hermes source:
  - directory plugins need root `plugin.yaml` and root `__init__.py` with `register(ctx)`
  - `hermes plugins install owner/repo` clones the GitHub repo into `~/.hermes/plugins/<manifest name>`
  - standalone user plugins are opt-in via `hermes plugins enable <name>`
  - pip plugins can expose `hermes_agent.plugins` entry points

## Objective

Build a GitHub-installable Hermes plugin and PyPI-ready Python package that classifies proposed memory writes before mutation. Phase 1 is dry-run/shadow mode only. It returns auditable routing decisions and never writes to Hermes memory, Mnemosyne, config, providers, gateway, or project files.

## MemSkill stance

This project takes precedence as the Hermes memory-policy implementation lane. MemSkill is an architectural influence and possible future optional backend, not a phase-1 runtime dependency. The core package must stay installable with `dependencies = []` until the plugin API and evaluator stabilize.

## Phase 1 scope — current scaffold

- Root Hermes plugin manifest: `plugin.yaml`
- Root plugin loader: `__init__.py`
- Python package under `src/hermes_memory_policy_gate/`
- Deterministic policy engine
- Offline evaluator against canned scenarios
- Tests for policy routing, evaluator, manifest, and plugin registration shape
- README, license, after-install note, CI scaffold

## Policy output contract

Every decision returns:

- `tier`
- `reason_codes`
- `confidence`
- `source`
- `provenance`
- `approval_required`
- `verification_step`
- `dry_run`
- `would_mutate`
- `notes`

Allowed tiers:

- `no_write_clean_field_boundary`
- `user_memory`
- `mnemosyne_global`
- `mnemosyne_session`
- `skill_patch`
- `project_artifact`
- `session_search_only`
- `superseded_update`
- `noisy_memory_invalidation`

## Forbidden in phase 1

- No Hermes core mutation
- No live memory writes
- No Mnemosyne writes/invalidations
- No skill patching
- No project-file mutation outside this repo
- No credentials/config/provider/gateway changes
- No hard MemSkill dependency
- No GitHub publication until approved
- No PyPI publication until plugin API and evaluator stabilize

## Acceptance gate before GitHub publication

- `python -m compileall src tests __init__.py`
- `python -m pytest -q` or `python -m unittest discover -s tests`
- `python -m hermes_memory_policy_gate.evaluator scenarios/memory_routing_cases.json --json`
- local `git status --short` reviewed
- Dr. Mani approves GitHub repo creation/publication

## Next implementation phase

1. Add more scenario coverage from real Hermes/Archimedes memory-routing failures.
2. Add optional JSONL audit log output, still local-only and opt-in.
3. Add install smoke against a disposable `HERMES_HOME`.
4. Add `hermes plugins install bionicbutterfly13/hermes-memory-policy-gate` docs after GitHub repo exists.
5. Only after stable GitHub plugin behavior: decide whether to publish PyPI package.
