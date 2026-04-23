from __future__ import annotations

from app.bootstrap import create_application


def main() -> None:
    bot = create_application()
    container = getattr(bot, "app_container")
    bot.run(container.settings.discord_token)


if __name__ == "__main__":
    main()
