# Rich Rule Log Guide

This skill documents the "Context-Aware Rule Log" system, which allows related game events (e.g., an ability trigger and its resulting effects) to be visually grouped together in the UI.

## Architecture

The system follows a three-tier architecture:

1.  **Engine (Rust)**: Tracks a `current_execution_id`. 
    - When an ability activation starts, the engine generates a new ID: `state.generate_execution_id()`.
    - Every log call while this ID is active is prefixed with `[ID: X]`.
    - When activation ends, ID is cleared: `state.clear_execution_id()`.

2.  **Frontend (JavaScript)**: `ui_logs.js` parses the `[ID: X]` tags.
    - Logs with the same ID are grouped into a `log-group-block`.
    - The first entry (Trigger) becomes the **Header**.
    - Subsequent entries (Effects) become nested **Details**.

3.  **Styling (CSS)**: `main.css` provides the visual hierarchy.
    - `.log-group-block`: The container for a grouped activation.
    - `.group-header`: Distinguished styling for the trigger event.
    - `.log-group-details`: Nested container for internal effects.

## Workflow: Adding New Logs

When adding a new log in the Rust engine:
- If it's a rule-level check, use `self.log_rule("RULE_NAME", "message")`.
- If it's inside an interpreter opcode, simply use `self.log("message")`. The `execution_id` will be automatically attached if an ability is active.

## Verification

To verify that tagging is working correctly:
1.  Run `python tools/verify_log_grouping.py`.
2.  Check that the raw output contains `[ID: N]`.
3.  In the web UI, verify that the logs are visually grouped and nested.

## Key Files
- `engine_rust_src/src/core/logic/game.rs`: Log formatting logic.
- `engine_rust_src/src/core/logic/state.rs`: `UIState` with execution ID fields.
- `frontend/web_ui/js/ui_logs.js`: Grouping and rendering logic.
- `frontend/web_ui/css/main.css`: Grouping styles.
