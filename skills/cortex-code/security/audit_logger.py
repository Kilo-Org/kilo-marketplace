"""Structured JSON audit logging with rotation."""
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class AuditLogger:
    """Audit logger with structured JSON format and file rotation.

    Note: This implementation is designed for single-process use only.
    Concurrent writes from multiple processes may result in interleaved
    JSON lines or race conditions during rotation. For multi-process
    scenarios, consider using a log aggregation service or file locking.
    """

    VERSION = "2.0.0"

    def __init__(
        self,
        log_path: Path,
        rotation_size: str = "10MB",
        retention_days: int = 30
    ):
        """Initialize audit logger.

        Args:
            log_path: Path to audit log file
            rotation_size: Size threshold for rotation (e.g., "10MB", "1GB")
            retention_days: Days to retain rotated logs (NOT YET IMPLEMENTED)
        """
        self.log_path = Path(log_path)
        self.rotation_size = self._parse_size(rotation_size)
        self.retention_days = retention_days
        self.initialization_error: Optional[str] = None
        # TODO: Implement cleanup of rotated files older than retention_days

        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

            if not self.log_path.exists():
                self.log_path.touch(mode=0o600)
            else:
                os.chmod(self.log_path, 0o600)
        except OSError as exc:
            self.initialization_error = str(exc)

    def log_execution(
        self,
        event_type: str,
        user: str,
        routing: Dict[str, Any],
        execution: Dict[str, Any],
        result: Dict[str, Any],
        session_id: Optional[str] = None,
        cortex_session_id: Optional[str] = None,
        security: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a cortex execution event."""
        if self.initialization_error:
            raise OSError(self.initialization_error)

        audit_id = str(uuid.uuid4())

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": self.VERSION,
            "audit_id": audit_id,
            "event_type": event_type,
            "user": user,
            "session_id": session_id,
            "cortex_session_id": cortex_session_id,
            "routing": routing,
            "execution": execution,
            "result": result,
            "security": security or {}
        }

        entry["prev_hash"] = self._last_entry_hash()
        entry["entry_hash"] = self._entry_hash(entry)

        self._write_entry(entry)
        self._rotate_if_needed()

        return audit_id

    def _entry_hash(self, entry: Dict[str, Any]) -> str:
        """Hash a canonical audit entry for tamper-evident chaining."""
        payload = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    def _last_entry_hash(self) -> Optional[str]:
        """Return the previous entry hash if the audit log has entries."""
        if not self.log_path.exists():
            return None
        try:
            last_line = None
            with open(self.log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        last_line = line
            if not last_line:
                return None
            return json.loads(last_line).get("entry_hash")
        except (OSError, json.JSONDecodeError):
            return None

    def _write_entry(self, entry: Dict[str, Any]) -> None:
        """Write entry to log file as JSON.

        Opens file for each write to avoid holding file handles open long-term.
        This trades some efficiency for simplicity and crash-safety (no buffering).
        If file was deleted externally, it will be recreated with default permissions.
        """
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes."""
        size_str = size_str.upper()
        multipliers = {
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024
        }

        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                try:
                    value = float(size_str[:-len(suffix)])
                    return int(value * multiplier)
                except ValueError:
                    pass

        # Default to bytes
        try:
            return int(size_str)
        except ValueError:
            return 10 * 1024 * 1024  # Default 10MB

    def _rotate_if_needed(self) -> None:
        """Rotate log file if exceeds size limit."""
        if not self.log_path.exists():
            return

        size = self.log_path.stat().st_size
        if size >= self.rotation_size:
            # Rotate: rename current to .1, .1 to .2, etc.
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            rotated_path = self.log_path.with_suffix(f".{timestamp}.log")
            self.log_path.rename(rotated_path)

            # Create new log file
            self.log_path.touch(mode=0o600)
