"""Print the amir monorepo welcome banner."""

from __future__ import annotations

import os


def main() -> int:
    """Emit the greet banner (used by ``poe greet`` / ``poe check``)."""
    user = os.environ.get("USER", "friend")
    print(
        f"Welcome to amir ♡♡♡ {user} ♡♡♡ ...\n\n"
        " █████╗ ███╗   ███╗██╗██████╗\n"
        "██╔══██╗████╗ ████║██║██╔══██╗\n"
        "███████║██╔████╔██║██║██████╔╝\n"
        "██╔══██║██║╚██╔╝██║██║██╔══██╗\n"
        "██║  ██║██║ ╚═╝ ██║██║██║  ██║\n"
        "╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═╝",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
