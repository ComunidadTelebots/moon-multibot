"""Static, non-executing analysis of scripts shared through Telegram."""

import re
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".lua", ".py", ".js", ".mjs", ".cjs", ".ts", ".php", ".rb",
    ".sh", ".bash", ".ps1", ".pl", ".go", ".java", ".cs", ".txt",
}
MAX_SCRIPT_BYTES = 2 * 1024 * 1024

PATTERNS = {
    "telegram": [
        r"telegram", r"telethon", r"pyrogram", r"tdlib", r"gramjs",
        r"getupdates", r"api\.telegram\.org", r"initdataunsafe",
    ],
    "identifiers": [
        r"user[_-]?id", r"sender[_-]?id", r"from_user\.id", r"from\.id",
        r"peer[_-]?id", r"message\.sender", r"effective_user\.id",
    ],
    "enumeration": [
        r"iter_participants", r"get_participants", r"get_chat_members",
        r"search_chat_members", r"getchatadministrators", r"getchatmember",
        r"channels\.getparticipants", r"messages\.search",
    ],
    "storage": [
        r"io\.open", r"open\s*\([^\n]+[wa][bt]?['\"]", r"writefile",
        r"appendfile", r"json\.dump", r"csv\.writer", r"sqlite",
        r"insert\s+into", r"table\.insert",
    ],
    "exfiltration": [
        r"requests\.(post|put)", r"fetch\s*\([^\n]+method\s*:\s*['\"]post",
        r"axios\.(post|put)", r"http[s]?\.request", r"webhook", r"socket\.",
        r"curl\s+[^\n]*(-d|--data)",
    ],
    "obfuscation": [
        r"loadstring", r"string\.char", r"fromcharcode", r"base64.*decode",
        r"eval\s*\(", r"exec\s*\(", r"marshal\.loads", r"compile\s*\(",
    ],
}


def _matches(text: str, category: str) -> list[str]:
    return [pattern for pattern in PATTERNS[category] if re.search(pattern, text, re.IGNORECASE)]


def analyze_script(path, file_name="") -> dict:
    """Score a source file without importing, evaluating or executing it."""
    source = Path(path)
    extension = Path(file_name or source.name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        return {"analyzed": False, "reason": "unsupported_extension", "score": 0, "verdict": "unknown"}
    if source.stat().st_size > MAX_SCRIPT_BYTES:
        return {"analyzed": False, "reason": "file_too_large", "score": 0, "verdict": "review"}

    raw = source.read_bytes()
    if b"\x00" in raw[:8192]:
        return {"analyzed": False, "reason": "binary_content", "score": 20, "verdict": "review"}
    text = raw.decode("utf-8", errors="ignore")
    evidence = {category: _matches(text, category) for category in PATTERNS}
    candidate_ids = sorted({
        match
        for match in re.findall(r"(?<!\d)(\d{5,19})(?!\d)", text)
        if int(match) > 0
    }, key=lambda value: (len(value), value))[:20]

    score = 0
    if evidence["telegram"] and evidence["identifiers"]:
        score += 30
    if evidence["enumeration"]:
        score += 35
    if evidence["storage"] and evidence["identifiers"]:
        score += 20
    if evidence["exfiltration"] and evidence["identifiers"]:
        score += 35
    if evidence["obfuscation"]:
        score += 20
    score = min(100, score)

    if score >= 80:
        verdict = "block"
    elif score >= 50:
        verdict = "review"
    else:
        verdict = "clean"
    categories = [name for name, matches in evidence.items() if matches]
    return {
        "analyzed": True,
        "score": score,
        "verdict": verdict,
        "extension": extension,
        "categories": categories,
        "evidence_count": sum(len(matches) for matches in evidence.values()),
        "candidate_ids": candidate_ids,
        "reason": "telegram_id_harvesting" if verdict in {"block", "review"} else "no_collection_pattern",
    }
