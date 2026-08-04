#!/usr/bin/env python3
"""
Reads recent Cortex Code session files for context enrichment.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

MAX_SESSION_BYTES = 5 * 1024 * 1024

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from security.prompt_sanitizer import PromptSanitizer


def find_recent_sessions(limit=3):
    """Find the most recent Cortex session files."""
    sessions_dir = Path.home() / ".local/share/cortex/sessions"

    if not sessions_dir.exists():
        print(f"Sessions directory not found: {sessions_dir}", file=sys.stderr)
        return []

    # Find all .jsonl session files
    session_files = sorted(
        [f for f in sessions_dir.glob("**/*.jsonl")],
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    return session_files[:limit]


def parse_session_file(session_path, sanitize=True):
    """Parse a session JSONL file and extract key information.

    Args:
        session_path: Path to the session JSONL file
        sanitize: Whether to sanitize PII from text content (default: True)

    Returns:
        Dictionary with session data, or None on error
    """
    try:
        if session_path.stat().st_size > MAX_SESSION_BYTES:
            print(f"Skipping oversized session file: {session_path}", file=sys.stderr)
            return None

        # Initialize sanitizer if needed
        sanitizer = PromptSanitizer() if sanitize else None

        session_data = {
            "session_id": None,
            "timestamp": session_path.stat().st_mtime,
            "user_prompts": [],
            "assistant_responses": [],
            "tools_used": [],
            "result": None
        }

        with open(session_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    event = json.loads(line)
                    event_type = event.get("type")

                    if event_type == "system" and event.get("subtype") == "init":
                        session_data["session_id"] = event.get("session_id")

                    elif event_type == "user":
                        # Check if this is a tool result or user message
                        message = event.get("message", {})
                        content = message.get("content", [])

                        # Extract user text if present
                        for item in content:
                            if item.get("type") == "text":
                                text = item.get("text", "")
                                # Sanitize user prompts if enabled
                                if sanitizer:
                                    text = sanitizer.sanitize(text)
                                session_data["user_prompts"].append(text)

                    elif event_type == "assistant":
                        message = event.get("message", {})
                        content = message.get("content", [])

                        for item in content:
                            if item.get("type") == "text":
                                text = item.get("text", "")
                                # Sanitize assistant responses if enabled
                                if sanitizer:
                                    text = sanitizer.sanitize(text)
                                session_data["assistant_responses"].append(text)
                            elif item.get("type") == "tool_use":
                                tool_name = item.get("name")
                                if tool_name:
                                    session_data["tools_used"].append(tool_name)

                    elif event_type == "result":
                        session_data["result"] = event.get("result")

                except json.JSONDecodeError:
                    continue

        return session_data

    except Exception as e:
        print(f"Error parsing session {session_path}: {e}", file=sys.stderr)
        return None


def summarize_sessions(session_files, sanitize=True):
    """Summarize recent Cortex sessions.

    Args:
        session_files: List of session file paths
        sanitize: Whether to sanitize PII from text content (default: True)

    Returns:
        List of session summary dictionaries
    """
    summaries = []

    for session_path in session_files:
        session_data = parse_session_file(session_path, sanitize=sanitize)

        if not session_data:
            continue

        # Create a concise summary
        # Note: session_data already has sanitized content if sanitize=True
        summary = {
            "file": session_path.name,
            "session_id": session_data["session_id"],
            "time": datetime.fromtimestamp(session_data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
            "prompts_count": len(session_data["user_prompts"]),
            "tools_used": list(set(session_data["tools_used"])),
            "last_prompt": session_data["user_prompts"][-1] if session_data["user_prompts"] else None,
            "result_type": type(session_data["result"]).__name__ if session_data["result"] else None
        }

        summaries.append(summary)

    return summaries


def main():
    """Main function to read and summarize recent Cortex sessions."""
    parser = argparse.ArgumentParser(description="Read recent Cortex sessions")
    parser.add_argument("--limit", type=int, default=3, help="Number of recent sessions to read")
    parser.add_argument("--verbose", action="store_true", help="Include full session details")
    parser.add_argument("--no-sanitize", action="store_true", help="Disable PII sanitization (for debugging)")
    args = parser.parse_args()

    # Determine if sanitization should be enabled (default: True)
    sanitize = not args.no_sanitize

    # Find recent sessions
    session_files = find_recent_sessions(args.limit)

    if not session_files:
        print("No recent Cortex sessions found", file=sys.stderr)
        return 0

    print(f"Found {len(session_files)} recent sessions", file=sys.stderr)

    # Summarize sessions with sanitization flag
    summaries = summarize_sessions(session_files, sanitize=sanitize)

    # Output JSON
    print(json.dumps(summaries, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
