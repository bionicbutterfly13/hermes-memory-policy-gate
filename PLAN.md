# Hermes Memory Policy Gate — Local Project Plan

Author: Mani Saint-Victor, MD / bionicbutterfly13
Lane: Hermes/Archimedes memory hygiene plugin
Status: GitHub-published plugin with narrow returned-block enforcement for `session_search_only` and user-memory boundary attempts; Phase 5 memory-tool caller contract in local workspace

## Source of truth

- Active local source clone: `/Users/manisaintvictor/.hermes/plugins/hermes-memory-policy-gate`
- GitHub remote: `https://github.com/bionicbutterfly13/hermes-memory-policy-gate.git`
- Hermes plugin contract verified from local Hermes source:
  - directory plugins need root `plugin.yaml` and root `__init__.py` with `register(ctx)`
  - `hermes plugins install owner/repo` clones the GitHub repo into `~/.hermes/plugins/<manifest name>`
  - standalone user plugins are opt-in via `hermes plugins enable <name>`
  - pip plugins can expose `hermes_agent.plugins` entry points

## Objective

Build a GitHub-installable Hermes plugin and PyPI-ready Python package that classifies proposed memory writes before mutation. The current plugin returns auditable routing decisions, blocks attempted durable writes for `session_search_only` when non-dry-run evaluation is explicitly requested, blocks attempts to force stale task-progress content into `user_memory`, maps Hermes live write entrypoints for Phase 4 harness coverage, defines a Phase 5 non-writing caller contract for the built-in `memory_tool` surface, and never writes to Hermes memory, Mnemosyne, config, providers, gateway, skills, or project files outside this plugin repo.

## MemSkill stance

This project takes precedence as the Hermes memory-policy implementation lane. MemSkill is an architectural influence and possible future optional backend, not a phase-1 runtime dependency. The core package must stay installable with `dependencies = []` until the plugin API and evaluator stabilize.

## Current plugin scope

- Root Hermes plugin manifest: `plugin.yaml`
- Root plugin loader: `__init__.py`
- Python package under `src/hermes_memory_policy_gate/`
- Deterministic policy engine
- Narrow no-write enforcement contract for `session_search_only`
- Narrow user-memory boundary contract for stale task-progress write attempts
- Offline evaluator against canned scenarios, including Phase 4 live-write-intent harness cases
- Phase 4 entrypoint map: `docs/phase4-live-write-entrypoints.md`
- Phase 5 built-in memory-tool caller contract: `docs/phase5-memory-tool-caller-contract.md`
- Non-writing `memory_tool_contract.py` planner for `blocked=true`, `approval_required=true`, and advisory passthrough behavior
- Tests for policy routing, evaluator, manifest, plugin registration shape, and Phase 5 caller contract
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

## Phase 4 mapped live write entrypoints

Read-only source mapping from `/Users/manisaintvictor/.hermes/hermes-agent` identified the live write surfaces a future interceptor would need to guard:

- built-in curated memory: `tools/memory_tool.py::memory_tool`, `MemoryStore.add`, `replace`, `remove`, and `_write_file`
- memory provider/Mnemosyne-style lifecycle: `MemoryManager.sync_all`, `on_session_end`, `on_pre_compress`, `on_memory_write`, and provider hooks in `agent/memory_provider.py`
- skill/procedural memory: `tools/skill_manager_tool.py` create/edit/patch/delete/supporting-file paths
- project artifacts: `tools/file_tools.py::write_file_tool` and `patch_tool`
- transcript recall fallback: `tools/session_search_tool.py::session_search`

The map is documented in `docs/phase4-live-write-entrypoints.md`. Current harness coverage models these as live-write-intent metadata only; it does not wire or mutate the Hermes source checkout.

## Phase 5 selected caller contract

Phase 5 selects the built-in curated memory surface only:

- surface: `memory_tool`
- entrypoint: `tools.memory_tool.memory_tool`
- write path: `builtin_memory_tool`
- contract module: `src/hermes_memory_policy_gate/memory_tool_contract.py`
- documentation: `docs/phase5-memory-tool-caller-contract.md`

The caller contract returns a non-writing `MemoryToolCallerPlan`:

- `blocked=true` -> `caller_action=block_original_memory_write`, `call_original=false`
- `approval_required=true` -> `caller_action=require_explicit_approval`, `call_original=false`
- advisory decision -> `caller_action=advisory_passthrough`, `call_original=true`

This is not Hermes core wiring. The contract does not import or call `tools.memory_tool`, does not touch `MemoryStore`, and does not write `USER.md` or `MEMORY.md`.

## Forbidden without separate approval

- No Hermes core mutation
- No live memory writes; `session_search_only` and user-memory boundary enforcement are returned block decisions only
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

1. Review Phase 5 caller-contract results and decide whether to approve a separate Hermes-core integration track for `tools.memory_tool.memory_tool` only.
2. If approved later, add core RED tests in `/Users/manisaintvictor/.hermes/hermes-agent` before wiring any live interceptor.
3. Keep actual writes disabled in this plugin; the plugin remains a decision/contract package, not a writer.
4. Do not expand Phase 5 behavior to Mnemosyne, skill patches, project artifacts, provider lifecycle hooks, gateway, or config without a separate named approval.
5. Add optional JSONL audit log output, still local-only and opt-in.
6. Add install smoke against a disposable `HERMES_HOME` before any release-tag workflow.
7. Reload or restart Hermes only after explicit approval if live tool surfaces must pick up a new schema.
8. Keep GitHub install docs current with the plugin manifest and CLI behavior.
9. Only after stable GitHub plugin behavior: decide whether to publish a PyPI package.
