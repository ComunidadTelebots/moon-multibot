"""Build the reviewed static Telegram blocklist from a numeric text export."""

import argparse
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    raw = args.source.read_text(encoding="utf-8")
    tokens = re.findall(r"\d+", raw)
    ids = sorted({int(token) for token in tokens if 0 < int(token) < 10**20})
    if not ids:
        raise SystemExit("No valid Telegram IDs found")

    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(
        "# Independent user-supplied Telegram blocklist; one numeric user ID per line.\n"
        "# Source: telegram_legacy. Imported as unverified moderation data.\n"
        "# List date: 2016-09-24 (24 de septiembre de 2016).\n"
        + "\n".join(str(user_id) for user_id in ids)
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(ids)} unique IDs to {args.destination}")


if __name__ == "__main__":
    main()
