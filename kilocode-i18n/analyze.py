import re
import json
import sys

def parse_ts_dict(content):
    """Extract key-value pairs from a TypeScript dict file."""
    pairs = {}
    
    # Match patterns like:  "key": "value",   or   "key": "value with {{template}}",
    # Also handle multi-line strings
    # Remove the import line and the export wrapper
    
    # Find all key-value entries
    # Pattern to match "key": "value" where value can be multiline
    pattern = r'"([^"]+)":\s*(?:"((?:[^"\\]|\\.)*)"|`((?:[^`\\]|\\.)*)`)'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        key = match.group(1)
        value = match.group(2) if match.group(2) is not None else match.group(3)
        # Unescape basic escapes
        value = value.replace('\\n', '\n').replace('\\"', '"').replace("\\\\", "\\")
        pairs[key] = value
    
    return pairs

def get_english_only_values(en_pairs, lang_pairs):
    """Find keys in lang_pairs that have same value as English (potentially untranslated)."""
    same_as_english = {}
    for key, en_value in en_pairs.items():
        if key in lang_pairs and lang_pairs[key] == en_value:
            same_as_english[key] = en_value
    return same_as_english

import os

workdir = sys.argv[1] if len(sys.argv) > 1 else "."

with open(f"{workdir}/en.ts", "r") as f:
    en_content = f.read()
en_pairs = parse_ts_dict(en_content)
print(f"English: {len(en_pairs)} keys")

languages = ["ar", "br", "bs", "da", "de", "es", "fr", "ja", "ko", "nl", "no", "pl", "ru", "th", "tr", "uk", "zh", "zht"]

for lang in languages:
    with open(f"{workdir}/{lang}.ts", "r") as f:
        content = f.read()
    lang_pairs = parse_ts_dict(content)
    same = get_english_only_values(en_pairs, lang_pairs)
    print(f"\n{lang}: {len(lang_pairs)} keys, {len(same)} potentially untranslated:")
    for key, value in same.items():
        print(f"  [{key}]: {repr(value[:80])}")

