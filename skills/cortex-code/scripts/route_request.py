#!/usr/bin/env python3
"""
Routing logic to determine whether a request belongs in Cortex Code or the host coding agent.
Uses semantic understanding rather than simple keyword matching.
"""

import json
import sys
import argparse
import fnmatch
import re
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for security imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from security.config_manager import ConfigManager
from security.cache_manager import CacheManager


# Snowflake/Cortex indicators
SNOWFLAKE_INDICATORS = [
    "snowflake", "cortex", "warehouse", "snowpark", "data warehouse",
    "cortex ai", "cortex search", "cortex analyst", "dynamic table",
    "snowflake database", "snowflake schema", "snowflake table",
    "data governance", "data quality", "trust my data",
    "ml function", "classification", "forecasting"
]

# Non-Snowflake indicators (keep in the host coding agent)
SNOWFLAKE_CONTEXT_TERMS = ["snowflake", "warehouse", "cortex", "schema", "table", "database"]
AMBIGUOUS_SNOWFLAKE_TERMS = ["stream", "task", "stage", "pipe"]
PATH_TOKEN_PATTERN = re.compile(r'(?<![\w.-])(?:~/?|/|\./|\.\./|[A-Za-z0-9_.-]+/)[A-Za-z0-9_./$~:-]+|(?<![\w.-])(?:\.ssh|\.aws|\.snowflake|\.env(?:\.[\w-]+)?|credentials\.(?:json|ya?ml)|[A-Za-z0-9_.-]+_key\.(?:p8|pem))(?![\w.-])', re.IGNORECASE)

CODING_AGENT_INDICATORS = [
    "local file", "git", "github", "commit", "push", "pull request",
    "python script", "javascript", "react", "frontend", "backend",
    "postgres", "mysql", "mongodb", "redis",
    "docker", "kubernetes", "infrastructure",
    "read file", "write file", "edit file", "create file"
]


def load_cortex_capabilities():
    """Load cached Cortex capabilities using CacheManager."""
    try:
        # Get cache directory from config
        config_manager = ConfigManager()
        cache_dir_str = config_manager.get("security.cache_dir")
        cache_dir = Path(cache_dir_str).expanduser()

        # Use CacheManager to read cache with integrity validation
        cache_manager = CacheManager(cache_dir)
        capabilities = cache_manager.read("cortex-capabilities")

        if capabilities is None:
            print("Warning: Cortex capabilities not cached. Run discover_cortex.py first.", file=sys.stderr)
            return {}

        return capabilities

    except Exception as e:
        print(f"Warning: Failed to load Cortex capabilities from cache: {e}", file=sys.stderr)
        print("Run discover_cortex.py to cache capabilities.", file=sys.stderr)
        return {}


def analyze_with_llm_logic(prompt, capabilities):
    """
    Analyze prompt using LLM-inspired logic.
    This is a deterministic approximation of what an LLM would consider.
    """
    prompt_lower = prompt.lower()

    # Score based on indicators
    snowflake_score = 0
    coding_agent_score = 0

    # Check for explicit Snowflake/Cortex mentions
    for indicator in SNOWFLAKE_INDICATORS:
        if indicator in prompt_lower:
            snowflake_score += 3 if indicator in ["snowflake", "cortex"] else 1

    # Ambiguous Snowflake object names only count with Snowflake context.
    if any(context in prompt_lower for context in SNOWFLAKE_CONTEXT_TERMS):
        for term in AMBIGUOUS_SNOWFLAKE_TERMS:
            if term in prompt_lower:
                snowflake_score += 1

    # Check for non-Snowflake indicators
    for indicator in CODING_AGENT_INDICATORS:
        if indicator in prompt_lower:
            coding_agent_score += 2

    # Check against Cortex skill triggers
    for skill_name, skill_info in capabilities.items():
        for trigger in skill_info.get("triggers", []):
            trigger_lower = trigger.lower()
            if trigger_lower in prompt_lower or any(word in prompt_lower for word in trigger_lower.split()):
                snowflake_score += 2
                break

    # SQL query detection
    sql_keywords = ["select", "insert", "update", "delete", "create table", "alter", "drop"]
    if any(kw in prompt_lower for kw in sql_keywords):
        # Could be any database, but check for Snowflake context
        if any(ind in prompt_lower for ind in ["snowflake", "warehouse", "cortex"]):
            snowflake_score += 3
        else:
            # Generic SQL, likely not Snowflake
            coding_agent_score += 1

    # Data-related terms (ambiguous, need context)
    data_terms = ["data quality", "schema", "table", "database", "query"]
    data_term_count = sum(1 for term in data_terms if term in prompt_lower)
    if data_term_count >= 2:
        # Multiple data terms suggest database work
        # Check if Snowflake context exists
        if snowflake_score > 0:
            snowflake_score += 2

    # Calculate confidence
    total_score = snowflake_score + coding_agent_score
    if total_score == 0:
        # No strong indicators, default to the host coding agent for safety.
        # The generic route value keeps the package independent of the host agent.
        return "coding_agent", 0.5

    confidence = max(snowflake_score, coding_agent_score) / total_score

    if snowflake_score > coding_agent_score:
        return "cortex", confidence
    else:
        return "coding_agent", confidence


def check_credential_allowlist(
    prompt: str,
    config_path: Optional[Path] = None,
    org_policy_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Check if prompt contains credential file paths from the allowlist.

    This function runs before routing analysis to block prompts that reference
    credential files, regardless of whether they would be routed to Cortex or the host agent.

    Args:
        prompt: User prompt to check
        config_path: Path to user config file (optional)
        org_policy_path: Path to organization policy file (optional)

    Returns:
        Dict with blocking decision:
        - blocked: True if credential detected, False otherwise
        - route: "blocked" if blocked, None otherwise
        - confidence: 1.0 if blocked (100% confident in blocking)
        - reason: Human-readable reason for blocking
        - pattern_matched: The allowlist pattern that matched
    """
    # Initialize ConfigManager with optional config paths
    config_manager = ConfigManager(
        config_path=config_path,
        org_policy_path=org_policy_path
    )

    # Load credential allowlist
    credential_allowlist = config_manager.get("security.credential_file_allowlist")

    prompt_tokens = PATH_TOKEN_PATTERN.findall(prompt)
    normalized_tokens = []
    for token in prompt_tokens:
        normalized_tokens.append(token)
        if token.startswith("~"):
            normalized_tokens.append(token.replace("~", str(Path.home()), 1))

    for pattern in credential_allowlist:
        expanded_pattern = str(Path(pattern).expanduser())
        candidate_patterns = [pattern, expanded_pattern]
        if pattern.startswith("~/**/"):
            candidate_patterns.append("**/" + pattern.split("~/**/", 1)[1])
        for token in normalized_tokens:
            token_lower = token.lower()
            for candidate_pattern in candidate_patterns:
                pattern_lower = candidate_pattern.lower()
                pattern_dir = pattern_lower.split("*")[0].rstrip("/")
                if (
                    fnmatch.fnmatch(token_lower, pattern_lower)
                    or fnmatch.fnmatch(f"*/{token_lower}", pattern_lower)
                    or (token_lower in {".ssh", ".aws", ".snowflake"} and pattern_dir.endswith(token_lower))
                ):
                    return {
                        "blocked": True,
                        "route": "blocked",
                        "confidence": 1.0,
                        "reason": f"Prompt contains credential file path from allowlist",
                        "pattern_matched": pattern
                    }

    # No credentials detected
    return {
        "blocked": False
    }


def main():
    """Main routing function."""
    parser = argparse.ArgumentParser(description="Route request to Cortex or the host coding agent")
    parser.add_argument("--prompt", required=True, help="User prompt to analyze")
    parser.add_argument("--config", help="Path to user config file")
    parser.add_argument("--org-policy", help="Path to organization policy file")
    args = parser.parse_args()

    # Step 1: Check credential allowlist BEFORE routing
    config_path = Path(args.config) if args.config else None
    org_policy_path = Path(args.org_policy) if args.org_policy else None

    credential_check = check_credential_allowlist(
        args.prompt,
        config_path,
        org_policy_path
    )

    # If blocked by credential check, return immediately
    if credential_check.get("blocked"):
        print(json.dumps(credential_check, indent=2))
        print(f"\n⛔ BLOCKED: Credential file detected", file=sys.stderr)
        print(f"   Pattern: {credential_check['pattern_matched']}", file=sys.stderr)
        print(f"   Reason: {credential_check['reason']}", file=sys.stderr)
        sys.exit(0)

    # Step 2: Load Cortex capabilities
    capabilities = load_cortex_capabilities()

    # Step 3: Analyze prompt for routing
    route, confidence = analyze_with_llm_logic(args.prompt, capabilities)

    # Step 4: Output decision
    result = {
        "route": route,
        "confidence": confidence,
        "reasoning": f"Routed to {route} with {confidence:.2%} confidence"
    }

    print(json.dumps(result, indent=2))

    print(f"\n→ Route to: {route.upper()}", file=sys.stderr)
    print(f"   Confidence: {confidence:.2%}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
