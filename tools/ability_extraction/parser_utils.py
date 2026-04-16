"""
Parser utilities for ability extraction.
This module contains pure utility functions for text processing, regex extraction,
and normalization used across the parsing pipeline.
"""
import re

# Precompiled regex patterns for performance
DIGIT_PATTERN = re.compile(r'(\d+)')
COUNT_PATTERN = re.compile(r'(\d+)枚')
PEOPLE_PATTERN = re.compile(r'(\d+)人')
GROUP_PATTERN = re.compile(r"『(.+?)』")
QUOTED_NAME_PATTERN = re.compile(r'「(.+?)」')
COST_PATTERN = re.compile(r'コスト(\d+)')
HEART_PATTERN = re.compile(r'{{heart_(\d+)\.png\|heart\d+}}')
BLADE_PATTERN = re.compile(r'{{icon_blade\.png\|ブレード}}')


def extract_int(pattern, text, default=None):
    """Extract an integer from text using a pattern or regex.
    
    Args:
        pattern: Regex pattern or string pattern to search for
        text: Text to search in
        default: Default value if no match found
    
    Returns:
        Extracted integer or default value
    """
    if isinstance(pattern, str):
        match = re.search(pattern, text)
    else:
        match = pattern.search(text)
    
    if match:
        return int(match.group(1))
    return default


def extract_group_name(text):
    """Extract group name from text (e.g., 『虹ヶ咲』 -> 虹ヶ咲)."""
    match = GROUP_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def extract_quoted_name(text):
    """Extract quoted name from text (e.g., 「上原歩夢」 -> 上原歩夢)."""
    match = QUOTED_NAME_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def has_any(text, phrases):
    """Check if text contains any of the given phrases."""
    return any(phrase in text for phrase in phrases)


def strip_suffix_period(text):
    """Remove trailing period from text."""
    return text.rstrip('。')


def strip_prefix_period(text):
    """Remove leading period from text."""
    return text.lstrip('。')


def parse_optional_flag(text, phrases):
    """Check if text contains optional phrases and return boolean.
    
    Args:
        text: Text to check
        phrases: List of phrases that indicate optional (e.g., ['でもよい', 'てもよい'])
    
    Returns:
        True if any optional phrase found, False otherwise
    """
    return any(phrase in text for phrase in phrases)


def normalize_whitespace(text):
    """Normalize whitespace in text - collapse multiple spaces to single space."""
    return re.sub(r'\s+', ' ', text).strip()


def normalize_fullwidth_digits(text):
    """Normalize full-width digits to half-width (e.g., １ -> 1)."""
    # Full-width digits: ０１２３４５６７８９
    fullwidth = '０１２３４５６７８９'
    halfwidth = '0123456789'
    translation = str.maketrans(fullwidth, halfwidth)
    return text.translate(translation)


def normalize_text(text):
    """Apply all normalization steps to text.
    
    This includes:
    - Whitespace cleanup
    - Full-width digit normalization
    - Trailing punctuation trimming
    
    Args:
        text: Text to normalize
    
    Returns:
        Normalized text
    """
    text = normalize_whitespace(text)
    text = normalize_fullwidth_digits(text)
    text = strip_suffix_period(text)
    return text


def extract_count(text):
    """Extract count from text (e.g., '3枚' -> 3, '2人' -> 2)."""
    # Try card count first
    match = COUNT_PATTERN.search(text)
    if match:
        return int(match.group(1))
    
    # Try people count
    match = PEOPLE_PATTERN.search(text)
    if match:
        return int(match.group(1))
    
    return None


def extract_cost(text):
    """Extract cost value from text (e.g., 'コスト3' -> 3)."""
    match = COST_PATTERN.search(text)
    if match:
        return int(match.group(1))
    return None


def extract_heart_types(text):
    """Extract heart types from text (e.g., heart icons)."""
    matches = HEART_PATTERN.findall(text)
    return matches if matches else None


def extract_blade_count(text):
    """Extract blade count from text (number of blade icons)."""
    matches = BLADE_PATTERN.findall(text)
    return len(matches) if matches else 0


def create_fallback(raw_text):
    """Create a fallback result with raw_text.
    
    This provides a consistent envelope for unparsed text.
    
    Args:
        raw_text: Original text that couldn't be parsed
    
    Returns:
        Dictionary with 'raw_text' key
    """
    return {'raw_text': raw_text}


def is_fallback(result):
    """Check if a result is a fallback (contains raw_text)."""
    return isinstance(result, dict) and 'raw_text' in result


def merge_position_requirement(result, action):
    """Merge position_requirement from action into result if present.
    
    This is used when position requirements are extracted at action level
    but should be at the result level.
    
    Args:
        result: Result dictionary to merge into
        action: Action dictionary to merge from
    
    Returns:
        Modified result dictionary
    """
    if 'position_requirement' in action:
        result['position_requirement'] = action['position_requirement']
        del action['position_requirement']
    return result


def split_commas_smartly(text):
    """Split text by commas, but preserve structural commas.
    
    Structural commas (should NOT split):
    - Subject markers: "は、" (wa particle)
    - Duration prefixes: "ライブ終了時まで、" (until end of live)
    - Time markers: "時、" (when) in certain contexts
    - Condition markers: "場合、" (if)
    
    Action separators (should split):
    - Sequence markers: "その後、" (after that)
    - Verb connectors: "し、" (and then)
    
    Args:
        text: Text to split
    
    Returns:
        List of text parts
    """
    parts = []
    current = ""
    i = 0
    while i < len(text):
        if text[i] == '、':
            # Check if this is a structural comma
            # Look ahead to see what precedes this comma
            if i >= 1:
                prev_char = text[i-1]
                # Subject marker: "は、"
                if prev_char == 'は':
                    current += '、'
                    i += 1
                    continue
                # Duration prefix: "ライブ終了時まで、"
                if i >= 7 and text[i-7:i] == 'ライブ終了時まで':
                    current += '、'
                    i += 1
                    continue
                # Condition marker: "場合、"
                if i >= 2 and text[i-2:i] == '場合':
                    current += '、'
                    i += 1
                    continue
            # Action separator: "その後、"
            if i >= 3 and text[i-3:i] == 'その後':
                parts.append(current)
                current = ""
                i += 1
                continue
            # Default: split on comma
            parts.append(current)
            current = ""
            i += 1
        else:
            current += text[i]
            i += 1
    
    if current:
        parts.append(current)
    
    return parts


def split_periods_smartly(text):
    """Split text by periods, but preserve periods in parentheses.
    
    This is a placeholder for future enhancement to handle multi-sentence
    patterns before splitting.
    
    Args:
        text: Text to split
    
    Returns:
        List of text parts
    """
    # For now, simple split by period
    # Future enhancement: detect multi-sentence patterns and handle them
    return text.split('。')


def extract_all_groups(text):
    """Extract all group names from text (『...』 patterns).
    
    Args:
        text: Text to search in
    
    Returns:
        List of group names, or empty list if none found
    """
    matches = GROUP_PATTERN.findall(text)
    return matches if matches else []


def extract_all_quoted_names(text):
    """Extract all quoted names from text (「...」 patterns).
    
    Args:
        text: Text to search in
    
    Returns:
        List of quoted names, or empty list if none found
    """
    matches = QUOTED_NAME_PATTERN.findall(text)
    return matches if matches else []
