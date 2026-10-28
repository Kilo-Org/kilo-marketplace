#!/usr/bin/env python3
"""
Executes Cortex Code in headless mode with streaming output parsing.
Uses --output-format stream-json for streaming results.
Handles tool use events and final results.
"""

import json
import os
import subprocess
import sys
import argparse
import threading
import queue
import time
from pathlib import Path
from typing import List, Dict, Optional

try:
    from security.prompt_sanitizer import PromptSanitizer
except Exception:
    PromptSanitizer = None


# Known tools for inversion logic (allowed -> disallowed)
KNOWN_TOOLS = [
    "Read", "Write", "Edit", "Bash", "Grep", "Glob",
    "snowflake_sql_execute", "data_diff", "snowflake_query"
]

DESTRUCTIVE_SHELL_TOOLS = [
    "Bash",
    "Bash(rm *)", "Bash(rm -rf *)", "Bash(rm -r *)",
    "Bash(sudo *)", "Bash(chmod 777 *)",
    "Bash(git push *)", "Bash(git reset --hard *)"
]

READ_ONLY_TOOLS = ["Edit", "Write", "Bash"] + DESTRUCTIVE_SHELL_TOOLS
UNKNOWN_TOOL_SENTINEL = "*"


def _redact_error_output(error_text: str) -> str:
    """Redact sensitive data before returning/logging error output."""
    if PromptSanitizer is None:
        return error_text
    return PromptSanitizer().sanitize(error_text)


def invert_tools_to_disallowed(allowed_tools: List[str]) -> List[str]:
    """
    Convert allowed tools list to disallowed tools list.

    For prompt mode: when security wrapper predicts/approves specific tools,
    we need to invert the list to block all OTHER tools via --disallowed-tools.

    Args:
        allowed_tools: List of tool names that ARE allowed

    Returns:
        List of tool names that should be disallowed (inverse of allowed)

    Example:
        allowed = ["Read", "Grep"]
        disallowed = ["Write", "Edit", "Bash", "Glob", ...other tools...]
    """
    inverted = [tool for tool in KNOWN_TOOLS if tool not in allowed_tools]
    inverted.append(UNKNOWN_TOOL_SENTINEL)
    return inverted


def execute_cortex_streaming(prompt: str, connection: Optional[str] = None,
                             disallowed_tools: Optional[List[str]] = None,
                             envelope: str = "RW",
                             approval_mode: str = "prompt",
                             allowed_tools: Optional[List[str]] = None,
                             timeout_seconds: int = 300,
                             deploy_confirmed: bool = False) -> Dict:
    """
    Execute Cortex with streaming JSON output in programmatic mode.

    Uses --output-format stream-json for streaming results.
    Tools are controlled via --disallowed-tools blocklists for safety.

    Args:
        prompt: The enriched prompt to send to Cortex
        connection: Optional Snowflake connection name
        disallowed_tools: Optional list of tools to explicitly block
        envelope: Security envelope mode (RO, RW, RESEARCH, DEPLOY, NONE)
        approval_mode: Approval mode (prompt, auto, envelope_only)
        allowed_tools: Optional list of tools that ARE allowed (for prompt mode)

    Returns:
        Dictionary with execution results
    """
    if approval_mode in ["auto", "envelope_only"] and envelope == "NONE":
        raise ValueError("NONE envelope is not allowed in auto or envelope_only approval modes")
    if approval_mode in ["auto", "envelope_only"] and envelope == "DEPLOY" and not deploy_confirmed:
        raise ValueError("DEPLOY envelope requires explicit confirmation")

    # Build command in print mode. The prompt is delivered with -p; do not add
    # --input-format stream-json here. Cortex treats that flag as JSON stdin
    # input mode, so combining it with -p and closed stdin can emit only the
    # initial session event and exit before the prompt is processed.
    cmd = [
        "cortex",
        "-p", prompt,
        "--output-format", "stream-json"
    ]

    # Add connection if specified
    if connection:
        cmd.extend(["-c", connection])

    # Step 1: Handle approval mode — build disallowed tools list for envelope security.
    # Do NOT use --allowed-tools: it creates a "must match pattern" check that
    # blocks Snowflake MCP tools.
    final_disallowed_tools = disallowed_tools or []

    if approval_mode == "prompt":
        # Prompt mode: invert allowed_tools to disallowed_tools
        # In prompt mode, we ONLY use allowed_tools (don't merge with envelope)
        if allowed_tools is not None:
            # User approved specific tools - block everything else
            inverted_tools = invert_tools_to_disallowed(allowed_tools)
            # Merge with existing disallowed tools (but NOT envelope tools)
            final_disallowed_tools = list(set(final_disallowed_tools) | set(inverted_tools))
        else:
            # No tools approved - block all known tools
            final_disallowed_tools = list(set(final_disallowed_tools) | set(KNOWN_TOOLS))

    elif approval_mode in ["envelope_only", "auto"]:
        # Envelope-only or auto mode: apply envelope-based security via blocklist.
        envelope_tools = []
        if envelope == "RO":
            # Read-only: block all write operations
            envelope_tools = READ_ONLY_TOOLS
        elif envelope in ["RW", "DEPLOY"]:
            # RW and DEPLOY may allow shell usage, but still block destructive
            # shell patterns by default. Explicit custom disallowed_tools can
            # add stricter policy on top.
            envelope_tools = DESTRUCTIVE_SHELL_TOOLS
        elif envelope == "RESEARCH":
            # Research: read-only plus web access
            envelope_tools = READ_ONLY_TOOLS
        # Merge envelope tools with final disallowed list
        if envelope_tools:
            final_disallowed_tools = list(set(final_disallowed_tools) | set(envelope_tools))

    # Step 3: Add final disallowed tools to command
    if final_disallowed_tools:
        for tool in final_disallowed_tools:
            cmd.extend(["--disallowed-tools", tool])

    debug_cmd = f"cortex -p \"...\" --output-format stream-json"
    if connection:
        debug_cmd += f" -c {connection}"
    if final_disallowed_tools:
        debug_cmd += f" --disallowed-tools {' '.join(final_disallowed_tools[:3])}{'...' if len(final_disallowed_tools) > 3 else ''}"
    print(debug_cmd, file=sys.stderr)

    process = None
    stderr_lines = []

    def _read_stderr(stderr):
        if stderr is None:
            return
        for stderr_line in stderr:
            stderr_lines.append(stderr_line)

    def _kill_process():
        if not process:
            return
        process.kill()
        try:
            process.wait(timeout=1)
        except Exception:
            pass

    try:
        # Start process. stdin=DEVNULL prevents accidental reads from the parent
        # terminal; prompt delivery is handled exclusively by -p print mode.
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )

        stderr_thread = threading.Thread(target=_read_stderr, args=(process.stderr,), daemon=True)
        stderr_thread.start()

        results = {
            "session_id": None,
            "events": [],
            "permission_requests": [],
            "final_result": None,
            "error": None
        }

        stdout_queue = queue.Queue()
        stdout_errors = queue.Queue()

        def _read_stdout(stdout):
            if stdout is None:
                stdout_queue.put(None)
                return
            try:
                for stdout_line in stdout:
                    stdout_queue.put(stdout_line)
            except Exception as exc:
                stdout_errors.put(exc)
            finally:
                stdout_queue.put(None)

        stdout_thread = threading.Thread(target=_read_stdout, args=(process.stdout,), daemon=True)
        stdout_thread.start()

        timed_out = False
        deadline = time.monotonic() + timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break

            try:
                line = stdout_queue.get(timeout=remaining)
            except queue.Empty:
                timed_out = True
                break

            if line is None:
                if not stdout_errors.empty():
                    raise stdout_errors.get()
                break

            if not line.strip():
                continue

            try:
                event = json.loads(line)
                results["events"].append(event)

                event_type = event.get("type")

                # Extract session ID
                if event_type == "system" and event.get("subtype") == "init":
                    results["session_id"] = event.get("session_id")
                    print(f"→ Started Cortex session: {results['session_id']}", file=sys.stderr)

                # Handle assistant responses
                elif event_type == "assistant":
                    message = event.get("message", {})
                    content = message.get("content", [])

                    for item in content:
                        if item.get("type") == "text":
                            print(f"[Cortex] {item.get('text', '')}", file=sys.stderr)

                        elif item.get("type") == "tool_use":
                            tool_name = item.get("name")
                            print(f"[Cortex] Using tool: {tool_name}", file=sys.stderr)

                # Handle permission requests (via user messages with tool_result containing denials)
                elif event_type == "user":
                    message = event.get("message", {})
                    content = message.get("content", [])

                    for item in content:
                        if item.get("type") == "tool_result":
                            tool_content = item.get("content", "")
                            tool_content_text = json.dumps(tool_content) if isinstance(tool_content, list) else str(tool_content)
                            if "Permission denied" in tool_content_text or "denied" in tool_content_text.lower():
                                results["permission_requests"].append({
                                    "tool_use_id": item.get("tool_use_id"),
                                    "content": tool_content
                                })
                                print(f"[Cortex] Permission request detected: {tool_content_text}", file=sys.stderr)

                # Handle final result
                elif event_type == "result":
                    results["final_result"] = event.get("result")
                    print(f"[Cortex] Result: {event.get('result')}", file=sys.stderr)

            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line: {line[:100]}... Error: {e}", file=sys.stderr)
                continue

        if timed_out:
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout_seconds)

        # Wait for process to complete
        process.wait(timeout=timeout_seconds)
        stderr_thread.join(timeout=1)

        # Check for errors
        if process.returncode != 0:
            stderr_output = _redact_error_output("".join(stderr_lines))
            results["error"] = stderr_output
            print(f"Error: Cortex exited with code {process.returncode}", file=sys.stderr)
            print(f"Stderr: {stderr_output}", file=sys.stderr)

        return results

    except subprocess.TimeoutExpired:
        _kill_process()
        return {
            "session_id": None,
            "events": [],
            "permission_requests": [],
            "final_result": None,
            "error": f"Cortex execution timed out after {timeout_seconds} seconds"
        }

    except Exception as e:
        _kill_process()
        return {
            "session_id": None,
            "events": [],
            "permission_requests": [],
            "final_result": None,
            "error": _redact_error_output(str(e))
        }


def _resolve_output_path(output_file: str) -> Path:
    """Resolve output path under a safe output directory."""
    base_dir = Path(os.environ.get("CORTEX_CODE_OUTPUT_DIR", Path.cwd())).expanduser().resolve()
    output_path = Path(output_file).expanduser()
    if not output_path.is_absolute():
        output_path = base_dir / output_path
    output_path = output_path.resolve()
    try:
        output_path.relative_to(base_dir)
    except ValueError as exc:
        raise ValueError(f"Output file must be under {base_dir}") from exc
    return output_path


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Execute Cortex Code headlessly")
    parser.add_argument("--prompt", required=True, help="Prompt to send to Cortex")
    parser.add_argument("--connection", "-c", help="Snowflake connection name")
    parser.add_argument("--disallowed-tools", nargs="+", help="Tools to explicitly block")
    parser.add_argument("--envelope", default="RW",
                       choices=["RO", "RW", "RESEARCH", "DEPLOY", "NONE"],
                       help="Security envelope mode (default: RW)")
    parser.add_argument("--approval-mode", default="prompt",
                       choices=["prompt", "auto", "envelope_only"],
                       help="Approval mode (default: prompt)")
    parser.add_argument("--allowed-tools", nargs="+",
                       help="Tools that are allowed (for prompt mode)")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Maximum seconds to wait for Cortex execution (default: 300)")
    parser.add_argument("--deploy-confirmed", action="store_true",
                       help="Required explicit confirmation for DEPLOY envelope in non-interactive modes")
    parser.add_argument("--output-file", help="Write JSON results to this file instead of stdout")
    parser.add_argument("--stream", action="store_true", help="Stream output (always true)")
    args = parser.parse_args()

    # Execute Cortex
    results = execute_cortex_streaming(
        args.prompt,
        connection=args.connection,
        disallowed_tools=args.disallowed_tools,
        envelope=args.envelope,
        approval_mode=args.approval_mode,
        allowed_tools=args.allowed_tools,
        timeout_seconds=args.timeout,
        deploy_confirmed=args.deploy_confirmed
    )

    # Output results as JSON
    output = json.dumps(results, indent=2)
    if args.output_file:
        try:
            output_path = _resolve_output_path(args.output_file)
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}, indent=2))
            return 1
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + "\n")
    else:
        print(output)

    # Exit with appropriate code
    if results.get("error"):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
