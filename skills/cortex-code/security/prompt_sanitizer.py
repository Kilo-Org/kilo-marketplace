"""Prompt sanitizer for PII removal and injection detection."""

import re
import unicodedata
from typing import List, Dict, Any


class PromptSanitizer:
    """Sanitizes prompts by removing PII and detecting injection attempts."""

    # PII regex patterns
    CREDIT_CARD_PATTERN = re.compile(
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b'  # Matches formats: 1234-5678-9012-3456 or 1234567890123456
    )

    SSN_PATTERN = re.compile(
        r'\b\d{3}-\d{2}-\d{4}\b|'  # Matches: 123-45-6789
        r'\b\d{9}\b'  # Matches: 123456789 (exactly 9 digits)
    )

    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )

    PHONE_PATTERN = re.compile(
        r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    )

    API_KEY_PATTERN = re.compile(
        r'\b(?:api[_-]?key|token|secret)\s*[:=]\s*["\']?[A-Za-z0-9_./+=-]{8,}["\']?|'
        r'\bsk-[A-Za-z0-9_./+=-]{8,}\b|'
        r'\b[A-Za-z0-9]{32,}\b',
        re.IGNORECASE,
    )

    ZERO_WIDTH_PATTERN = re.compile(r'[\u200B-\u200D\uFEFF]')
    HOMOGLYPH_TRANSLATION = str.maketrans({
        'а': 'a', 'А': 'A',  # Cyrillic a
        'е': 'e', 'Е': 'E',  # Cyrillic e
        'і': 'i', 'І': 'I',  # Cyrillic/Ukrainian i
        'о': 'o', 'О': 'O',  # Cyrillic o
        'р': 'p', 'Р': 'P',  # Cyrillic er
        'с': 'c', 'С': 'C',  # Cyrillic es
        'х': 'x', 'Х': 'X',  # Cyrillic ha
        'у': 'y', 'У': 'Y',  # Cyrillic u
    })

    # Injection detection patterns
    INJECTION_PATTERNS = [
        re.compile(r'ignore\s+(?:all\s+|the\s+)?(previous|above|prior)\s+(instructions|directions|prompts?)', re.IGNORECASE),
        re.compile(r'(enter|enable|activate)\s+developer\s+mode', re.IGNORECASE),
        re.compile(r'you\s+are\s+now\s+in\s+developer\s+mode', re.IGNORECASE),
        re.compile(r'disregard\s+(?:all\s+|the\s+)?(previous|above|prior)', re.IGNORECASE),
        re.compile(r'bypass\s+(restrictions|rules|guidelines)', re.IGNORECASE),
    ]

    def _normalize_for_detection(self, text: str) -> str:
        """Normalize text so obfuscated prompt injections match detection rules."""
        normalized = unicodedata.normalize('NFKC', text)
        normalized = self.ZERO_WIDTH_PATTERN.sub('', normalized)
        normalized = normalized.translate(self.HOMOGLYPH_TRANSLATION)
        normalized = ''.join(
            char for char in normalized
            if unicodedata.category(char) not in {'Cf', 'Mn'}
        )
        return normalized

    def sanitize(self, text: str) -> str:
        """
        Sanitize text by removing PII and detecting injection attempts.

        Args:
            text: The text to sanitize

        Returns:
            Sanitized text with PII removed and injection warnings added
        """
        if not text:
            return text

        detection_text = self._normalize_for_detection(text)

        # Check for injection attempts first
        for pattern in self.INJECTION_PATTERNS:
            if pattern.search(detection_text):
                return "[POTENTIAL INJECTION DETECTED - REMOVED]"

        # Remove PII
        text = self.CREDIT_CARD_PATTERN.sub('<CREDIT_CARD>', text)
        text = self.SSN_PATTERN.sub('<SSN>', text)
        text = self.EMAIL_PATTERN.sub('<EMAIL>', text)
        text = self.PHONE_PATTERN.sub('<PHONE>', text)
        text = self.API_KEY_PATTERN.sub('[API_KEY_REDACTED]', text)

        return text

    def sanitize_sql_literals(self, sql: str) -> str:
        """
        Sanitize SQL string by removing PII from literals.

        Args:
            sql: The SQL string to sanitize

        Returns:
            Sanitized SQL string
        """
        return self.sanitize(sql)

    def sanitize_history(self, history: List[Dict[str, Any]], max_items: int = 3) -> List[Dict[str, Any]]:
        """
        Sanitize conversation history by limiting items and removing PII.

        Args:
            history: List of conversation history items (dicts with 'role' and 'content')
            max_items: Maximum number of items to keep (default: 3)

        Returns:
            Sanitized and limited history list
        """
        if not history:
            return []

        # Keep only the last max_items
        limited_history = history[-max_items:] if len(history) > max_items else history

        # Sanitize each item's content
        sanitized = []
        for item in limited_history:
            sanitized_item = item.copy()
            if 'content' in sanitized_item:
                sanitized_item['content'] = self.sanitize(sanitized_item['content'])
            sanitized.append(sanitized_item)

        return sanitized
