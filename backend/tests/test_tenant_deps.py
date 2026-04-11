"""Tests for get_current_tenant_id resolution and enforcement."""

import unittest
import uuid
from types import SimpleNamespace

from fastapi import HTTPException

from app.api.deps import get_current_tenant_id
from app.models.tenant import TenantRole


class _Exec:
    def __init__(self, items):
        self._items = list(items)

    def all(self):
        return list(self._items)

    def first(self):
        return self._items[0] if self._items else None


class _FakeSession:
    """Minimal async session whose .exec returns a queued _Exec.

    Each call to .exec pops from the front of the queue so tests can
    drive the ordering of multiple queries in a single handler.
    """

    def __init__(self, queue):
        self._queue = list(queue)

    async def exec(self, _stmt):
        return self._queue.pop(0)


def _user(active_tenant_id=None):
    u = SimpleNamespace()
    u.id = uuid.uuid4()
    u.active_tenant_id = active_tenant_id
    return u


def _membership(tenant_id, user_id, role=TenantRole.member):
    return SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        role=role,
    )


class TestGetCurrentTenantId(unittest.IsolatedAsyncioTestCase):
    async def test_header_wins_over_active(self):
        user = _user(active_tenant_id=uuid.uuid4())
        header_tenant = uuid.uuid4()
        session = _FakeSession([_Exec([_membership(header_tenant, user.id)])])

        result = await get_current_tenant_id(
            x_tenant_id=str(header_tenant),
            current_user=user,
            session=session,
        )
        self.assertEqual(result, header_tenant)

    async def test_header_without_membership_forbids(self):
        user = _user()
        header_tenant = uuid.uuid4()
        session = _FakeSession([_Exec([])])  # no membership

        with self.assertRaises(HTTPException) as ctx:
            await get_current_tenant_id(
                x_tenant_id=str(header_tenant),
                current_user=user,
                session=session,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    async def test_header_invalid_uuid_400(self):
        user = _user()
        session = _FakeSession([])

        with self.assertRaises(HTTPException) as ctx:
            await get_current_tenant_id(
                x_tenant_id="not-a-uuid",
                current_user=user,
                session=session,
            )
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_falls_back_to_active_tenant_on_user(self):
        active = uuid.uuid4()
        user = _user(active_tenant_id=active)
        session = _FakeSession([_Exec([_membership(active, user.id)])])

        result = await get_current_tenant_id(
            x_tenant_id=None,
            current_user=user,
            session=session,
        )
        self.assertEqual(result, active)

    async def test_falls_back_to_first_membership(self):
        user = _user()  # no active tenant
        first_tenant = uuid.uuid4()
        session = _FakeSession([_Exec([_membership(first_tenant, user.id)])])

        result = await get_current_tenant_id(
            x_tenant_id=None,
            current_user=user,
            session=session,
        )
        self.assertEqual(result, first_tenant)

    async def test_no_memberships_at_all_forbids(self):
        user = _user()
        session = _FakeSession([_Exec([])])

        with self.assertRaises(HTTPException) as ctx:
            await get_current_tenant_id(
                x_tenant_id=None,
                current_user=user,
                session=session,
            )
        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
