# Phase 5 Memory Tool Caller Contract

Source of truth for this Phase 5 pass:

- Plugin workspace: `/Users/manisaintvictor/.hermes/plugins/hermes-memory-policy-gate`
- Selected write surface: built-in curated memory tool only
- Hermes source surface, read only: `tools.memory_tool.memory_tool`

Phase 5 is a caller-contract pass. It does not modify Hermes core, does not wrap live dispatch, and does not write to `USER.md`, `MEMORY.md`, Mnemosyne, skills, config, providers, or gateway state.

## Selected surface

Phase 5 chooses one write surface from the Phase 4 map:

```text
surface: memory_tool
entrypoint: tools.memory_tool.memory_tool
write_path: builtin_memory_tool
mutating actions: add, replace, remove
targets: user, memory
```

## Contract module

The local contract lives in:

```text
src/hermes_memory_policy_gate/memory_tool_contract.py
```

It exposes:

```python
build_memory_tool_policy_request(args)
plan_memory_tool_call(args)
```

`plan_memory_tool_call(args)` builds a non-dry-run policy request that models the moment before the original Hermes `memory` tool would mutate a file. It returns a `MemoryToolCallerPlan` and never calls the original memory tool.

## Caller actions

### 1. Policy returned `blocked=true`

Required caller behavior:

```text
caller_action=block_original_memory_write
call_original=false
policy_would_mutate=false
```

The original `memory_tool` call must not run. For stale task-progress content, the operator-facing route is transcript/session_search.

Examples:

- `Fixed bug X, submitted PR #123, and completed Phase 4 today.`
- `Remember that I submitted PR #123 and completed Phase 4 today.` with target `user`

### 2. Policy returned `approval_required=true`

Required caller behavior:

```text
caller_action=require_explicit_approval
call_original=false
policy_would_mutate=false
```

The original `memory_tool` call must not run until a source manifest or explicit approval is present.

Example:

- Unapproved clean-field / Quill / old-campaign material.

### 3. Advisory decision

Required caller behavior:

```text
caller_action=advisory_passthrough
call_original=true
policy_would_mutate=false
```

This is a design signal for a future interceptor. In this Phase 5 repo pass, no interceptor is wired, so no memory mutation occurs from this module.

Example:

- Durable user preference routed to `user_memory`.

## Safety invariants

Every Phase 5 caller-plan result must preserve:

- `policy_would_mutate=false`
- no import of Hermes `tools.memory_tool`
- no call to `MemoryStore`
- no file write
- no Mnemosyne write/invalidation
- no gateway/config/provider change
- no broader write-surface wiring

## Verification

Phase 5 tests:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -p no:cacheprovider tests/test_memory_tool_contract.py -q
```

Full local gate:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m compileall -q src tests __init__.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -p no:cacheprovider tests -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m hermes_memory_policy_gate scenarios/memory_routing_cases.json --json

git diff --check
git status --short --branch
git diff --name-only
```

Expected evaluator shape remains:

```text
failed=0
live_writes=false
```

## Explicitly out of scope

- Editing `/Users/manisaintvictor/.hermes/hermes-agent`
- Wrapping `agent/tool_executor.py`
- Restarting Hermes or the gateway
- Changing Hermes config
- Writing memory
- Pushing, tagging, or releasing
- Extending the contract to Mnemosyne, skill patches, project artifacts, or provider lifecycle hooks
