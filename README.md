# Hermes Memory Policy Gate

Author: Mani Saint-Victor, MD / bionicbutterfly13

`hermes-memory-policy-gate` is a MemSkill-inspired, dry-run memory policy gate for Hermes Agent.

It does not store memory. It decides where a proposed memory write *should* go and returns an auditable decision.

## Status

Phase 1: GitHub-installable shadow/dry-run plugin.

This plugin does not mutate Hermes core, credentials, providers, gateway, config, Mnemosyne, skills, or existing memory.

## MemSkill stance

This project is MemSkill-inspired, not MemSkill-dependent.

Phase 1 keeps `dependencies = []` so the Hermes plugin remains lightweight and GitHub-installable. MemSkill may become an optional backend later, behind the same auditable decision schema, after the plugin API and offline evaluator stabilize.

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

All output is advisory until a future explicitly approved integration phase wires decisions into live Hermes write paths.
