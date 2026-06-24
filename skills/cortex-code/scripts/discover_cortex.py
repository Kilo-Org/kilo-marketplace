#!/usr/bin/env python3
"""
Discovers Cortex Code capabilities by listing skills and parsing their metadata.
Caches results for the current CodingAgent session.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
import re

# Add parent directory to path for security imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from security.cache_manager import CacheManager
from security.config_manager import ConfigManager


def run_command(cmd):
    """Run a command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=False,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1


def discover_cortex_skills():
    """Discover all available Cortex Code skills."""
    print("Discovering Cortex Code capabilities...", file=sys.stderr)

    # Run cortex skill list
    stdout, stderr, code = run_command(["cortex", "skill", "list"])

    if code != 0:
        print(f"Error running cortex skill list: {stderr}", file=sys.stderr)
        return {}

    # Parse skill list output
    skills = {}

    # Handles two formats:
    # Old format: "skill-name /path/to/skill"
    # New format (v1.0.5.6+):
    #   [BUNDLED]
    #    - skill-name: /path/to/skill
    for line in stdout.strip().split('\n'):
        if not line.strip():
            continue

        # Skip section headers like [BUNDLED], [PROJECT], [GLOBAL]
        if re.match(r'^\[.*\]$', line.strip()):
            continue

        # New format: "  - skill-name: /path/to/skill"
        new_format_match = re.match(r'^\s*-\s+(\S+?):\s+', line)
        if new_format_match:
            skill_name = new_format_match.group(1).strip()
        else:
            # Old format: "skill-name /path/to/skill"
            parts = line.split()
            if not parts:
                continue
            skill_name = parts[0].strip(':').strip()

        # Read the skill's SKILL.md to get description and triggers
        skill_info = read_skill_metadata(skill_name)
        if skill_info:
            skills[skill_name] = skill_info

    return skills


def read_skill_metadata(skill_name):
    """Read SKILL.md frontmatter for a specific skill."""
    # Cortex bundled skills are typically in ~/.local/share/cortex/{version}/bundled_skills/
    cortex_share = Path.home() / ".local/share/cortex"

    # Find the most recent version directory
    if not cortex_share.exists():
        return None

    version_dirs = sorted([d for d in cortex_share.iterdir() if d.is_dir()], reverse=True)

    for version_dir in version_dirs:
        bundled_skills = version_dir / "bundled_skills"
        if not bundled_skills.exists():
            continue

        # Look for skill directory
        skill_path = bundled_skills / skill_name / "SKILL.md"
        if skill_path.exists():
            return parse_skill_md(skill_path)

    return None


def parse_skill_md(skill_path):
    """Parse SKILL.md file and extract frontmatter."""
    try:
        with open(skill_path, 'r') as f:
            content = f.read()

        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return None

        frontmatter = frontmatter_match.group(1)

        # Simple YAML parsing for name and description
        name_match = re.search(r'name:\s*(.+)', frontmatter)
        desc_match = re.search(r'description:\s*["\']?(.+?)["\']?$', frontmatter, re.MULTILINE | re.DOTALL)

        if name_match and desc_match:
            name = name_match.group(1).strip().strip('"\'')
            description = desc_match.group(1).strip().strip('"\'')

            # Extract "Use when" trigger patterns from body
            triggers = extract_triggers(content)

            return {
                "name": name,
                "description": description,
                "triggers": triggers
            }
    except Exception as e:
        print(f"Error parsing {skill_path}: {e}", file=sys.stderr)
        return None


def extract_triggers(content):
    """Extract trigger phrases from skill content."""
    triggers = []

    # Look for "Use when", "Trigger", "When to use" sections
    trigger_patterns = [
        r'(?:Use when|When to use|Trigger).*?:\s*(.+?)(?=\n\n|\#\#)',
        r'- Use (?:when|for|if):\s*(.+?)$'
    ]

    for pattern in trigger_patterns:
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            trigger_text = match.group(1).strip()
            # Clean up and split by common separators
            phrases = re.split(r'[,;]|\n-', trigger_text)
            triggers.extend([p.strip() for p in phrases if p.strip()])

    return triggers[:10]  # Limit to 10 most relevant triggers


def main():
    """Main discovery function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Discover Cortex Code capabilities")
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Cache directory for storing capabilities (default: from config or ~/.cache/cortex-skill)"
    )
    args = parser.parse_args()

    # Determine cache directory
    if args.cache_dir:
        cache_dir = args.cache_dir
    else:
        # Get default from config
        config_manager = ConfigManager()
        cache_dir_str = config_manager.get("security.cache_dir")
        cache_dir = Path(cache_dir_str).expanduser()

    # Discover capabilities
    capabilities = discover_cortex_skills()

    # Cache using CacheManager with SHA256 fingerprint validation
    try:
        cache_manager = CacheManager(cache_dir)
        cache_manager.write("cortex-capabilities", capabilities, ttl=86400)  # 24-hour TTL
        print(f"Discovered {len(capabilities)} Cortex skills", file=sys.stderr)
        print(f"Cached to: {cache_dir / 'cortex-capabilities.json'}", file=sys.stderr)
    except Exception as e:
        # If cache fails, log warning but continue
        print(f"Warning: Failed to cache capabilities: {e}", file=sys.stderr)
        print(f"Discovered {len(capabilities)} Cortex skills", file=sys.stderr)

    # Output the capabilities
    print(json.dumps(capabilities, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
