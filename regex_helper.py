import re

def extract_regex(pattern: str, source: str) -> list[str] | None:
    match = re.search(pattern, source)
    return list(match.groups()) if match else None
