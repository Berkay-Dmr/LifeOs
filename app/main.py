from __future__ import annotations

import sys
from pathlib import Path

# Windows encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv


def main() -> None:
    # Load .env from current working directory
    load_dotenv()

    from app.cli.commands import cli
    cli()


if __name__ == "__main__":
    main()
