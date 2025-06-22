import re
from typing import Optional

def extract_regex(pattern: str, source: str) -> Optional[list[str]]:
    match = re.search(pattern, source)
    return list(match.groups()) if match else None
