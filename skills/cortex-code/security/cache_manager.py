"""Secure cache manager with integrity validation."""
import hashlib
import hmac
import json
import os
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class CacheManager:
    """Secure cache manager with fingerprint validation."""

    VERSION = "2.0.0"

    def __init__(self, cache_dir: Path):
        """Initialize cache manager."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Set directory permissions to 0700 (owner only). Some managed or
        # sandboxed filesystems deny chmod on existing home-cache directories;
        # keep the cache usable rather than failing security-wrapper startup.
        try:
            os.chmod(self.cache_dir, 0o700)
        except PermissionError as exc:
            warnings.warn(
                f"Could not set secure permissions on cache directory {self.cache_dir}: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )

    def _signature_key(self) -> bytes:
        """Return key material for cache tamper detection."""
        return os.environ.get(
            "CORTEX_CODE_CACHE_HMAC_KEY",
            f"cortex-cache:{self.cache_dir}"
        ).encode()

    def _calculate_signature(self, cache_entry: dict) -> str:
        """Calculate HMAC over stable cache fields."""
        signed_payload = {
            "version": cache_entry.get("version"),
            "created_at": cache_entry.get("created_at"),
            "expires_at": cache_entry.get("expires_at"),
            "data": cache_entry.get("data"),
            "fingerprint": cache_entry.get("fingerprint"),
        }
        payload = json.dumps(signed_payload, sort_keys=True, separators=(",", ":"))
        return hmac.new(self._signature_key(), payload.encode(), hashlib.sha256).hexdigest()

    def _validate_key(self, key: str) -> None:
        """Validate cache key to prevent path traversal."""
        if not key:
            raise ValueError("Cache key cannot be empty")

        # Allow only alphanumeric, underscore, hyphen, and dot
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', key):
            raise ValueError(
                f"Invalid cache key: {key}. "
                f"Only alphanumeric characters, underscores, hyphens, and dots are allowed."
            )

        # Prevent path traversal
        if '..' in key or '/' in key or '\\' in key:
            raise ValueError(f"Invalid cache key: {key}. Path traversal not allowed.")

    def write(self, key: str, data: Any, ttl: int = 86400) -> None:
        """Write data to cache with TTL and fingerprint."""
        self._validate_key(key)

        cache_entry = {
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": time.time() + ttl,
            "data": data
        }

        # Calculate fingerprint
        data_str = json.dumps(data, sort_keys=True)
        fingerprint = hashlib.sha256(data_str.encode()).hexdigest()
        cache_entry["fingerprint"] = fingerprint
        cache_entry["signature"] = self._calculate_signature(cache_entry)

        # Write to file
        cache_file = self.cache_dir / f"{key}.json"
        with open(cache_file, 'w') as f:
            json.dump(cache_entry, f, indent=2)

        # Set file permissions to 0600 (owner read/write only)
        os.chmod(cache_file, 0o600)

    def read(self, key: str) -> Optional[Any]:
        """Read data from cache with validation."""
        self._validate_key(key)

        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                cache_entry = json.load(f)

            # Check expiration
            if cache_entry["expires_at"] <= time.time():
                # Expired - delete and return None
                cache_file.unlink(missing_ok=True)
                return None

            # Validate fingerprint
            data = cache_entry["data"]
            data_str = json.dumps(data, sort_keys=True)
            expected_fingerprint = hashlib.sha256(data_str.encode()).hexdigest()

            if cache_entry["fingerprint"] != expected_fingerprint:
                # Tampered - delete and return None
                cache_file.unlink(missing_ok=True)
                return None

            expected_signature = self._calculate_signature(cache_entry)
            if cache_entry.get("signature") != expected_signature:
                # Tampered - delete and return None
                cache_file.unlink(missing_ok=True)
                return None

            return data

        except (json.JSONDecodeError, KeyError, FileNotFoundError, OSError):
            # Corrupted cache - delete and return None
            cache_file.unlink(missing_ok=True)
            return None

    def clear(self, key: Optional[str] = None) -> None:
        """Clear cache entry or all entries."""
        if key:
            self._validate_key(key)
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink(missing_ok=True)
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink(missing_ok=True)
