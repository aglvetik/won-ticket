from __future__ import annotations

import pytest

from app.config import constants
from tests.fakes import FakeGuild, FakeMember, FakeRole


@pytest.mark.asyncio
async def test_accept_flow_removes_guest_adds_accept_roles_and_prefixes_nick(member_service) -> None:
    guest_role = FakeRole(constants.GUEST_ROLE_ID)
    accept_role_1 = FakeRole(constants.ACCEPT_ROLES_IDS[0])
    accept_role_2 = FakeRole(constants.ACCEPT_ROLES_IDS[1])
    guild = FakeGuild(roles=[guest_role, accept_role_1, accept_role_2])
    member = FakeMember(name="PlayerOne", roles=[guest_role])

    ok, message = await member_service.try_accept_roles_and_nick(guild, member)

    assert ok is True
    assert message == "Роли и ник обновлены."
    assert guest_role not in member.roles
    assert accept_role_1 in member.roles
    assert accept_role_2 in member.roles
    assert member.nick == f"{constants.CLAN_TAG} PlayerOne"
