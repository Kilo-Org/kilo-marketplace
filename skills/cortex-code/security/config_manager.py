"""Configuration manager with 3-layer precedence."""
import copy
import os
import sys
from pathlib import Path
from typing import Any, Optional, Dict
import yaml

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigManager:
    """Manages security configuration with precedence: org policy > user config > defaults."""

    DEFAULT_CONFIG = {
        "security": {
            "approval_mode": "prompt",
            "tool_prediction_confidence_threshold": 0.7,
            "allow_tool_expansion": True,
            "audit_log_path": "~/.__CODING_AGENT__/skills/cortex-code/audit.log",
            "audit_log_rotation": "10MB",
            "audit_log_retention": 30,
            "sanitize_conversation_history": True,
            "sanitize_session_files": True,
            "max_history_items": 3,
            "cache_dir": "~/.cache/cortex-skill",
            "cache_permissions": "0600",
            "allowed_envelopes": ["RO", "RW", "RESEARCH"],
            "deploy_envelope_confirmation": True,
            "execution_timeout_seconds": 300,
            "credential_file_allowlist": [
                "~/.ssh/*",
                "~/.snowflake/*",
                "**/.env",
                "**/.env.*",
                "**/credentials.json",
                "**/*_key.p8",
                "**/*_key.pem",
                "~/.aws/credentials",
                "~/.kube/config"
            ]
        }
    }

    def __init__(
        self,
        config_path: Optional[Path] = None,
        org_policy_path: Optional[Path] = None
    ):
        """Initialize config manager."""
        self._config = self._load_config(config_path, org_policy_path)

    def _validate_config(self, config: Dict) -> None:
        """Validate configuration values."""
        security = config.get("security", {})

        # Validate approval_mode
        approval_mode = security.get("approval_mode")
        if approval_mode not in ["prompt", "auto", "envelope_only"]:
            raise ConfigValidationError(
                f"Invalid approval_mode: {approval_mode}. "
                f"Must be one of: prompt, auto, envelope_only"
            )

        # Validate allowed_envelopes
        valid_envelopes = {"RO", "RW", "RESEARCH", "DEPLOY", "NONE"}
        allowed_envelopes = security.get("allowed_envelopes", [])
        for envelope in allowed_envelopes:
            if envelope not in valid_envelopes:
                raise ConfigValidationError(
                    f"Invalid envelope: {envelope}. "
                    f"Must be one of: {', '.join(valid_envelopes)}"
                )

        # Validate numeric values
        confidence = security.get("tool_prediction_confidence_threshold")
        if confidence is not None:
            if not isinstance(confidence, (int, float)):
                raise ConfigValidationError(
                    f"tool_prediction_confidence_threshold must be a number, got {type(confidence).__name__}"
                )
            if not (0 <= confidence <= 1):
                raise ConfigValidationError(
                    f"tool_prediction_confidence_threshold must be between 0 and 1, got {confidence}"
                )

        retention = security.get("audit_log_retention")
        if retention is not None:
            if not isinstance(retention, int):
                raise ConfigValidationError(
                    f"audit_log_retention must be an integer, got {type(retention).__name__}"
                )
            if retention < 0:
                raise ConfigValidationError(
                    f"audit_log_retention must be >= 0, got {retention}"
                )

    def _safe_placeholder_path(self, original_path: str) -> str:
        """Fallback when install-time __CODING_AGENT__ replacement was not applied."""
        suffix = Path(original_path).name or "audit.log"
        return str(Path.home() / ".cache" / "cortex-skill" / suffix)

    def _expand_paths(self, config: Dict) -> Dict:
        """Expand ~ and environment variables in file paths."""
        security = config.get("security", {})

        # Expand audit_log_path
        if "audit_log_path" in security:
            security["audit_log_path"] = os.path.expanduser(security["audit_log_path"])
            if "__CODING_AGENT__" in security["audit_log_path"]:
                security["audit_log_path"] = self._safe_placeholder_path(security["audit_log_path"])

        # Expand cache_dir
        if "cache_dir" in security:
            security["cache_dir"] = os.path.expanduser(security["cache_dir"])

        config["security"] = security
        return config

    def _load_config(
        self,
        config_path: Optional[Path],
        org_policy_path: Optional[Path]
    ) -> Dict:
        """Load configuration with 3-layer precedence."""
        # Start with defaults
        config = copy.deepcopy(self.DEFAULT_CONFIG)

        # Load user config if exists
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    try:
                        user_config = yaml.safe_load(f) or {}
                        config = self._merge_config(config, user_config)
                    except yaml.YAMLError as e:
                        print(f"Warning: Failed to parse user config {config_path}: {e}", file=sys.stderr)
            except OSError as e:
                print(f"Warning: Failed to read user config {config_path}: {e}", file=sys.stderr)

        org_policy_security = {}

        # Load org policy if exists
        if org_policy_path and org_policy_path.exists():
            try:
                with open(org_policy_path, 'r') as f:
                    try:
                        org_policy = yaml.safe_load(f) or {}
                        org_policy_security = org_policy.get("security", {}) or {}

                        # If override flag set, org policy wins completely
                        if org_policy.get("security", {}).get("override_user_config"):
                            # Merge org policy over defaults (skip user config)
                            config = self._merge_config(copy.deepcopy(self.DEFAULT_CONFIG), org_policy)
                        else:
                            # Normal merge: org policy > user config > defaults
                            config = self._merge_config(config, org_policy)
                    except yaml.YAMLError as e:
                        print(f"Warning: Failed to parse org policy {org_policy_path}: {e}", file=sys.stderr)
            except OSError as e:
                print(f"Warning: Failed to read org policy {org_policy_path}: {e}", file=sys.stderr)

        # Validate before applying floors so invalid user config is still rejected.
        self._validate_config(config)

        # User config must not relax the security floor unless org policy
        # explicitly authorizes the relaxed field/value.
        config = self._enforce_security_floor(config, org_policy_security)

        # Validate configuration
        self._validate_config(config)

        # Expand file paths
        config = self._expand_paths(config)

        return config

    def _enforce_security_floor(self, config: Dict, org_policy_security: Optional[Dict] = None) -> Dict:
        """Prevent user config from relaxing defaults without explicit org policy."""
        result = copy.deepcopy(config)
        security = result.setdefault("security", {})
        default_security = self.DEFAULT_CONFIG["security"]
        org_policy_security = org_policy_security or {}

        if (
            security.get("approval_mode") != default_security["approval_mode"]
            and "approval_mode" not in org_policy_security
        ):
            security["approval_mode"] = default_security["approval_mode"]

        default_envelopes = set(default_security["allowed_envelopes"])
        explicit_org_envelopes = set(org_policy_security.get("allowed_envelopes", []))
        envelope_floor = default_envelopes | explicit_org_envelopes
        requested_envelopes = security.get("allowed_envelopes", default_security["allowed_envelopes"])
        security["allowed_envelopes"] = [
            envelope for envelope in requested_envelopes
            if envelope in envelope_floor
        ]

        return result

    def _merge_config(self, base: Dict, override: Dict) -> Dict:
        """Deep merge override into base."""
        result = copy.deepcopy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key."""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value
