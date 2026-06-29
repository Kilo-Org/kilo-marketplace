#!/usr/bin/env python3
"""
Predicts which Cortex tools will be needed based on the user prompt and capabilities.
Enhanced with confidence scoring for approval handler.
"""

import json
import sys
import argparse
from pathlib import Path
from security.cache_manager import CacheManager
from security.config_manager import ConfigManager


# Tool prediction mappings with weighted patterns
TOOL_PATTERNS = {
    "snowflake_sql_execute": [
        "select", "insert", "update", "delete", "query", "sql",
        "table", "database", "data", "snowflake"
    ],
    "bash": [
        "run", "execute", "command", "script", "install", "shell"
    ],
    "read": [
        "read", "show", "display", "view", "check", "inspect", "examine"
    ],
    "write": [
        "create", "write", "generate", "save", "output", "file"
    ],
    "glob": [
        "find", "search", "list", "files", "directory", "locate"
    ],
    "grep": [
        "search", "find", "pattern", "match", "contains"
    ]
}


# Always include these base tools for Snowflake operations
BASE_SNOWFLAKE_TOOLS = ["snowflake_sql_execute", "bash", "read"]


def load_capabilities():
    """Load cached Cortex capabilities through CacheManager."""
    try:
        config_manager = ConfigManager()
        cache_dir = Path(config_manager.get("security.cache_dir")).expanduser()
        cache_manager = CacheManager(cache_dir)
        return cache_manager.read("cortex-capabilities") or {}
    except Exception as exc:
        print(f"Warning: Failed to load Cortex capabilities from cache: {exc}", file=sys.stderr)
        return {}


def predict_tools(prompt, envelope=None):
    """
    Predict required tools based on prompt analysis with confidence scoring.

    Args:
        prompt: User prompt to analyze
        envelope: Optional envelope dict with capabilities

    Returns:
        dict with:
            - tools: list of predicted tool names
            - confidence: float 0-1 indicating prediction confidence
            - reasoning: str explaining the prediction
    """
    prompt_lower = prompt.lower()
    predicted = set(BASE_SNOWFLAKE_TOOLS)
    matched_patterns = []

    # Check each tool pattern and track matches
    for tool, patterns in TOOL_PATTERNS.items():
        tool_matches = []
        for pattern in patterns:
            if pattern in prompt_lower:
                tool_matches.append(pattern)

        if tool_matches:
            predicted.add(tool)
            matched_patterns.append(f"{tool}: {', '.join(tool_matches)}")

    # Calculate confidence based on pattern matches
    total_words = len(prompt_lower.split())
    pattern_match_count = len(matched_patterns)

    # Base confidence on match density
    if total_words == 0:
        confidence = 0.5
    elif pattern_match_count == 0:
        # Only base tools predicted
        confidence = 0.5
    else:
        # More matches relative to prompt length = higher confidence
        confidence = min(0.9, 0.5 + (pattern_match_count / max(total_words / 5, 1)) * 0.4)

    # Adjust confidence based on prompt clarity
    if total_words < 5:
        confidence *= 0.8  # Short prompts are less clear
    elif total_words > 20:
        confidence *= 0.95  # Very detailed prompts slightly less confident

    # Check capabilities if provided in envelope
    if envelope and "capabilities" in envelope:
        capabilities = envelope["capabilities"]
        for skill_name, skill_info in capabilities.items():
            description = skill_info.get("description", "").lower()

            # If skill description matches prompt, boost confidence
            if any(word in description for word in prompt_lower.split()):
                confidence = min(1.0, confidence + 0.1)

                # Data quality skills typically need more tools
                if "quality" in skill_name or "governance" in skill_name:
                    predicted.update(["glob", "grep", "write"])
                    matched_patterns.append(f"skill_match: {skill_name}")

                # ML skills need bash for model operations
                if "ml" in skill_name or "machine" in skill_name or "forecast" in skill_name:
                    predicted.add("bash")
                    matched_patterns.append(f"skill_match: {skill_name}")

    # Generate reasoning
    if matched_patterns:
        reasoning = f"Matched {len(matched_patterns)} patterns: {'; '.join(matched_patterns[:3])}"
        if len(matched_patterns) > 3:
            reasoning += f" and {len(matched_patterns) - 3} more"
    else:
        reasoning = "Using base Snowflake tools only - no specific patterns matched"

    return {
        "tools": sorted(list(predicted)),
        "confidence": round(confidence, 2),
        "reasoning": reasoning
    }


def main():
    """Main tool prediction function."""
    parser = argparse.ArgumentParser(description="Predict required Cortex tools")
    parser.add_argument("--prompt", required=True, help="User prompt to analyze")
    args = parser.parse_args()

    # Load capabilities
    capabilities = load_capabilities()
    envelope = {"capabilities": capabilities} if capabilities else None

    # Predict tools with confidence
    result = predict_tools(args.prompt, envelope)

    # Output as JSON
    print(json.dumps(result, indent=2))

    # Summary to stderr
    print(f"\nPredicted {len(result['tools'])} tools with {result['confidence']:.0%} confidence:", file=sys.stderr)
    print(f"  Tools: {', '.join(result['tools'])}", file=sys.stderr)
    print(f"  Reasoning: {result['reasoning']}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
