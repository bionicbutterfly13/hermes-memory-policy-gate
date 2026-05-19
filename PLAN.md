# Hermes Memory Policy Gate — Local Project Plan

Author: Mani Saint-Victor, MD / bionicbutterfly13
Lane: Hermes/Archimedes memory hygiene plugin
Status: GitHub-published plugin with narrow `session_search_only` no-write enforcement; local source clone is the active implementation workspace

## Source of truth

- Active local source clone: `/Users/manisaintvictor/.hermes/plugins/hermes-memory-policy-gate`
- GitHub remote: `https://github.com/bionicbutterfly13/hermes-memory-policy-gate.git`
- Hermes plugin contract verified from local Hermes source:
  - directory plugins need root `plugin.yaml` and root `__init__.py` with `register(ctx)`
  - `hermes plugins install owner/repo` clones the GitHub repo into `~/.hermes/plugins/<manifest name>`
  - standalone user plugins are opt-in via `hermes plugins enable <name>`
  - pip plugins can expose `hermes_agent.plugins` entry points

## Objective

Build a GitHub-installable Hermes plugin and PyPI-ready Python package that classifies proposed memory writes before mutation. The current plugin returns auditable routing decisions, blocks attempted durable writes for `session_search_only` when non-dry-run evaluation is explicitly requested, and never writes to Hermes memory, Mnemosyne, config, providers, gateway, or project files.

## MemSkill stance

This project takes precedence as the Hermes memory-policy implementation lane. MemSkill is an architectural influence and possible future optional backend, not a phase-1 runtime dependency. The core package must stay installable with `dependencies = []` until the plugin API and evaluator stabilize.

## Current plugin scope

- Root Hermes plugin manifest: `plugin.yaml`
- Root plugin loader: `__init__.py`
- Python package under `src/hermes_memory_policy_gate/`
- Deterministic policy engine
- Narrow no-write enforcement contract for `session_search_only`
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
- `blocked`
- `enforced`
- `enforcement_action`
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

## Forbidden without separate approval

- No Hermes core mutation
- No live memory writes; `session_search_only` enforcement is a returned block decision only
- No Mnemosyne writes/invalidations
- No skill patching
- No project-file mutation outside this repo
- No credentials/config/provider/gateway changes
- No hard MemSkill dependency
- No GitHub push, release, or publication update until approved
- No PyPI publication until plugin API and evaluator stabilize

## Acceptance gate before push/release

- `PYTHONPATH=src python3 -m compileall -q src tests __init__.py`
- `PYTHONPATH=src python3 -m pytest tests -q` or `PYTHONPATH=src python3 -m unittest discover -s tests`
- `PYTHONPATH=src python3 -m hermes_memory_policy_gate scenarios/memory_routing_cases.json --json`
- local `git status --short` reviewed
- Dr. Mani approves the remote push/release action

## Next implementation phase

1. Add more scenario coverage from real Hermes/Archimedes memory-routing failures.
2. Add optional JSONL audit log output, still local-only and opt-in.
3. Add install smoke against a disposable `HERMES_HOME` before any release-tag workflow.
4. Reload or restart Hermes only after explicit approval if live tool surfaces must pick up the new schema.
5. Keep GitHub install docs current with the plugin manifest and CLI behavior.
6. Only after stable GitHub plugin behavior: decide whether to publish a PyPI package.
