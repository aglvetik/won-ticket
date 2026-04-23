from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(eq=True, frozen=True)
class FakeRole:
    id: int
    mention: str = ""

    def __post_init__(self) -> None:
        if not self.mention:
            object.__setattr__(self, "mention", f"<@&{self.id}>")


@dataclass
class FakeChannel:
    id: int
    name: str


@dataclass
class FakeCategory:
    id: int
    channels: list[FakeChannel] = field(default_factory=list)


class FakeGuild:
    def __init__(
        self,
        *,
        categories: list[FakeCategory] | None = None,
        channels: list[FakeChannel] | None = None,
        roles: list[FakeRole] | None = None,
    ) -> None:
        self._categories = {category.id: category for category in (categories or [])}
        self._channels = {channel.id: channel for channel in (channels or [])}
        self._roles = {role.id: role for role in (roles or [])}
        self.text_channels = list(channels or [])
        self.me = None
        self._state = type("State", (), {"user": None})()

    def get_channel(self, channel_id: int):
        return self._categories.get(channel_id) or self._channels.get(channel_id)

    def get_role(self, role_id: int) -> Optional[FakeRole]:
        return self._roles.get(role_id)


class FakeMember:
    def __init__(self, name: str, roles: list[FakeRole], nick: Optional[str] = None) -> None:
        self.name = name
        self.nick = nick
        self.roles = list(roles)
        self.removed_roles: list[FakeRole] = []
        self.added_roles: list[FakeRole] = []
        self.edited_nick: Optional[str] = None

    async def remove_roles(self, *roles: FakeRole, reason: str | None = None) -> None:
        del reason
        for role in roles:
            if role in self.roles:
                self.roles.remove(role)
                self.removed_roles.append(role)

    async def add_roles(self, *roles: FakeRole, reason: str | None = None) -> None:
        del reason
        for role in roles:
            if role not in self.roles:
                self.roles.append(role)
                self.added_roles.append(role)

    async def edit(self, *, nick: str, reason: str | None = None) -> None:
        del reason
        self.nick = nick
        self.edited_nick = nick
