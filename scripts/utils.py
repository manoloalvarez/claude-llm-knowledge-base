#!/usr/bin/env python3
"""Shared utilities for knowledge-wiki scripts."""


def extract_frontmatter(content):
    """Extract YAML frontmatter as a dict. Returns empty dict if none.

    Handles both inline lists (tags: [a, b]) and block-style lists:
        sources:
          - "[[raw/kindle/Book]]"
    """
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()
    result = {}
    current_key = None
    current_list = None
    for line in fm_text.split("\n"):
        stripped = line.strip()
        # Block-list item (e.g., "  - value")
        if stripped.startswith("- ") and current_key is not None and current_list is not None:
            item = stripped[2:].strip().strip('"').strip("'")
            current_list.append(item)
            continue
        # New key:value line
        if ":" in stripped and not stripped.startswith("-") and not stripped.startswith("#"):
            # Save any pending block list
            if current_key is not None and current_list is not None:
                result[current_key] = current_list
                current_list = None
                current_key = None
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if not value:
                # Start of a block list
                current_key = key
                current_list = []
            elif value.startswith("[") and value.endswith("]"):
                result[key] = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",") if v.strip()]
            else:
                result[key] = value
        elif not stripped:
            # Empty line ends block list
            if current_key is not None and current_list is not None:
                result[current_key] = current_list
                current_list = None
                current_key = None
    # Flush any remaining block list
    if current_key is not None and current_list is not None:
        result[current_key] = current_list
    return result
