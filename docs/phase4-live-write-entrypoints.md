# Phase 4 Live Write Interception Map

Source of truth for this map:

- Plugin workspace: `/Users/manisaintvictor/.hermes/plugins/hermes-memory-policy-gate`
- Hermes source checkout, read only: `/Users/manisaintvictor/.hermes/hermes-agent`

Phase 4 is a planning/harness pass. It does not wire the policy gate into Hermes core and does not perform memory writes.

## Mapped Hermes write entrypoints

### Built-in curated memory files

- Tool entrypoint: `tools/memory_tool.py::memory_tool`
- File-backed store: `tools/memory_tool.py::MemoryStore`
- Mutating methods:
  - `MemoryStore.add(target, content)` writes `MEMORY.md` or `USER.md` through `save_to_disk()`.
  - `MemoryStore.replace(target, old_text, new_content)` writes the selected store through `save_to_disk()`.
  - `MemoryStore.remove(target, old_text)` writes the selected store through `save_to_disk()`.
  - `MemoryStore._write_file(path, entries)` writes via temp file, fsync, and `atomic_replace()`.
- Agent dispatch paths observed:
  - `agent/agent_runtime_helpers.py` routes `function_name == "memory"` to `memory_tool()` and then notifies external providers via `agent._memory_manager.on_memory_write(...)` for `add` and `replace`.
  - `agent/tool_executor.py` contains the same memory-tool dispatch bridge.

Phase 4 harness status: model live-write intent with metadata such as `entrypoint=tools.memory_tool.memory_tool`, `write_path=builtin_memory_tool`, `action`, and `target`. Policy decisions must keep `would_mutate=false`.

### External memory providers / Mnemosyne-style provider paths

- Provider manager: `agent/memory_manager.py::MemoryManager`
- Provider contract: `agent/memory_provider.py::MemoryProvider`
- Provider registration: `agent/agent_init.py` loads one active provider from `memory.provider` and injects its tool schemas.
- Write-capable lifecycle hooks:
  - `MemoryProvider.sync_turn(user_content, assistant_content, session_id=...)`
  - `MemoryProvider.on_session_end(messages)`
  - `MemoryProvider.on_pre_compress(messages)`
  - `MemoryProvider.on_memory_write(action, target, content, metadata=None)`
  - `MemoryProvider.on_delegation(task, result, ...)`
- Manager fan-out points:
  - `MemoryManager.sync_all(...)`
  - `MemoryManager.on_session_end(...)`
  - `MemoryManager.on_pre_compress(...)`
  - `MemoryManager.on_memory_write(...)`

Phase 4 harness status: model provider live-write intent with metadata such as `entrypoint=agent.memory_manager.sync_all`, `write_path=memory_provider_sync_turn`, and requested tiers `mnemosyne_global` or `mnemosyne_session`. Policy decisions remain advisory/non-writing for these tiers.

### Skill/procedural memory writes

- Tool entrypoint: `tools/skill_manager_tool.py`
- Mutating functions observed:
  - `_create_skill(...)`
  - `_edit_skill(...)`
  - `_patch_skill(...)`
  - `_delete_skill(...)`
  - supporting-file `write_file` and `remove_file` paths
- Write primitives observed:
  - `_atomic_write_text(...)`
  - `shutil.rmtree(...)`
  - `Path.unlink(...)`

Phase 4 harness status: model skill live-write intent with metadata such as `entrypoint=tools.skill_manager_tool.skill_manage`, `write_path=skill_patch`, and `action=patch`. Policy decisions route reusable procedures to `skill_patch` but remain advisory/non-writing.

### Project artifact writes

- Tool entrypoints: `tools/file_tools.py::write_file_tool` and `tools/file_tools.py::patch_tool`
- Registry names: `write_file` and `patch`
- Mutating operations observed:
  - `file_ops.write_file(path, content)`
  - patch/replace flow through `patch_tool(...)`
  - file-state write tracking through `file_state.note_write(...)`

Phase 4 harness status: model project artifact live-write intent with metadata such as `entrypoint=tools.file_tools.write_file_tool`, `write_path=project_artifact`, and requested tier `project_artifact`. Policy decisions route project state to `project_artifact` but remain advisory/non-writing.

### Session search / transcript recall

- Recall tool: `tools/session_search_tool.py::session_search`
- Backing DB: `hermes_state.py::SessionDB`
- `session_search` is read/recall surface for historical transcript facts. It is not a durable memory-write target.

Phase 4 harness status: attempted durable writes for ephemeral task progress must route to `session_search_only` and may return `blocked=true`, `enforced=true`, and `enforcement_action=block_durable_write` when `dry_run=false`.

## Phase 4 non-writing contract

For every live-write-intent scenario in this phase:

- The evaluator may set `live_write_intent=true` for the scenario.
- The policy gate must return `would_mutate=false`.
- The evaluator report must keep `live_writes=false`.
- Non-`session_search_only` tiers remain advisory unless a later phase explicitly approves integration.
- `session_search_only` durable-write attempts may be enforced as returned blocks only.
- User-memory attempts containing stale task progress may be enforced as returned blocks only.

## Still out of scope after Phase 5 unless separately approved

- Modifying Hermes core dispatch paths.
- Wrapping `memory_tool`, `MemoryManager`, provider hooks, `skill_manage`, `write_file`, or `patch` with a live policy interceptor.
- Writing to USER.md, MEMORY.md, Mnemosyne, skills, project artifacts outside this plugin repo, config, providers, or gateway state.
- Restarting the gateway.
- Pushing, tagging, or releasing this repo.
