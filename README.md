# Hermes Memory Policy Gate

Author: Mani Saint-Victor, MD / bionicbutterfly13

`hermes-memory-policy-gate` is a MemSkill-inspired memory policy gate for Hermes Agent.

It does not store memory. It decides where a proposed memory write *should* go and returns an auditable decision.

## Status

GitHub-installable plugin with narrow returned-block enforcement for `session_search_only` and user-memory boundary attempts, plus Phase 4 live-write-interception planning/harness coverage.

The current enforcement contract blocks attempted durable-memory writes for ephemeral task progress when callers explicitly request non-dry-run evaluation. It also blocks attempts to force stale PR, issue, phase, or completed-task logs into `user_memory`. Durable user preferences, Mnemosyne global/session candidates, skill patches, project artifacts, and clean-field approval gates remain advisory and non-writing. Phase 4 adds mapped Hermes write entrypoints and evaluator scenarios for live-write intent without wiring any live interceptor.

This plugin does not mutate Hermes core, credentials, providers, gateway, config, Mnemosyne, skills, or existing memory.

## MemSkill stance

This project is MemSkill-inspired, not MemSkill-dependent.

The plugin keeps `dependencies = []` so it remains lightweight and GitHub-installable. MemSkill may become an optional backend later, behind the same auditable decision schema, after the plugin API and offline evaluator stabilize.

## Primary install target

Install from GitHub:

```bash
hermes plugins install bionicbutterfly13/hermes-memory-policy-gate
hermes plugins enable hermes-memory-policy-gate
```

Restart the gateway only if using it from gateway surfaces:

```bash
hermes gateway restart
```

## PyPI status

PyPI publishing is phase 2. This repository is PyPI-ready, but GitHub plugin installation is the primary distribution path until the plugin API and evaluator stabilize.

## What it classifies

Allowed routing tiers:

- `no_write_clean_field_boundary`
- `user_memory`
- `mnemosyne_global`
- `mnemosyne_session`
- `skill_patch`
- `project_artifact`
- `session_search_only`
- `superseded_update`
- `noisy_memory_invalidation`

## Tool surface

When enabled as a Hermes plugin, it registers the tool:

- `memory_policy_gate`

The tool accepts text/context/source/metadata and returns a JSON decision.

## Local evaluator

```bash
PYTHONPATH=src python3 -m hermes_memory_policy_gate scenarios/memory_routing_cases.json --json
```

The seed scenarios include non-dry-run returned-block cases and Phase 4 live-write-intent harness cases, so `dry_run_only=false` is expected; `live_writes=false` must remain true.

## Phase 4 live-write-interception map

Phase 4 mapped Hermes write entrypoints without changing Hermes core:

- built-in curated memory: `tools/memory_tool.py::memory_tool` and `MemoryStore` write methods
- provider/Mnemosyne-style paths: `MemoryManager.sync_all`, `on_session_end`, `on_pre_compress`, `on_memory_write`, and provider hooks
- procedural memory: `tools/skill_manager_tool.py` create/edit/patch/delete/supporting-file paths
- project artifacts: `tools/file_tools.py::write_file_tool` and `patch_tool`
- transcript recall: `tools/session_search_tool.py::session_search` as the read-only route for ephemeral task progress

Details are in `docs/phase4-live-write-entrypoints.md`.

## Development

```bash
PYTHONPATH=src python3 -m compileall -q src tests __init__.py
PYTHONPATH=src python3 -m unittest discover -s tests
```

Optional after installing dev extras:

```bash
PYTHONPATH=src python3 -m pytest tests -q
```

## Safety model

This is an evaluator and router. It is not a writer.

`session_search_only` decisions can enforce a no-write block when `dry_run=false`; user-memory boundary attempts can return `block_user_memory_write` when stale task-progress content is being forced into `user_memory`. Phase 4 live-write-intent scenarios still report `would_mutate=false` and evaluator `live_writes=false`. Every tier other than the returned-block cases remains advisory/dry-run until a future explicitly approved integration phase wires decisions into live Hermes write paths.
