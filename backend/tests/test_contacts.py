"""Unit and integration tests for Users Search and Contacts API."""

import pytest
from httpx import AsyncClient


async def create_and_verify_user(client: AsyncClient, phone: str, name: str) -> dict:
    """Helper fixture function to create, verify, and return user response."""
    await client.post("/api/v1/auth/register", json={"phone_number": phone, "display_name": name})
    await client.post("/api/v1/auth/verify", json={"phone_number": phone, "otp": "123456"})
    login_res = await client.post(
        "/api/v1/auth/login", json={"phone_number": phone, "otp": "123456"}
    )
    return login_res.json()["user"]


@pytest.mark.asyncio
async def test_unauthenticated_user_search_rejected(client: AsyncClient):
    """Verify unauthenticated user search returns 401."""
    res = await client.get("/api/v1/users/search?q=Alice")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_user_search_filtering_and_self_exclusion(client: AsyncClient):
    """Verify user search filters by query and excludes the authenticated searcher."""
    user1 = await create_and_verify_user(client, "+15551000001", "Alice Smith")

    # Logout to create user2
    await client.post("/api/v1/auth/logout")
    user2 = await create_and_verify_user(client, "+15551000002", "Alice Johnson")

    # Logout to create user3
    await client.post("/api/v1/auth/logout")
    user3 = await create_and_verify_user(client, "+15551000003", "Bob Williams")

    # Now login as user1 (Alice Smith) and search "Alice"
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": user1["phone_number"], "otp": "123456"}
    )

    res = await client.get("/api/v1/users/search?q=Alice")
    assert res.status_code == 200
    users = res.json()["users"]

    # Must contain user2 (Alice Johnson), but MUST EXCLUDE user1 (Alice Smith)
    user_ids = [u["id"] for u in users]
    assert user2["id"] in user_ids
    assert user1["id"] not in user_ids
    assert user3["id"] not in user_ids  # Bob Williams does not match "Alice"


@pytest.mark.asyncio
async def test_user_search_empty_and_no_match(client: AsyncClient):
    """Verify search with no matches returns empty list."""
    await create_and_verify_user(client, "+15551000010", "Searcher User")
    res = await client.get("/api/v1/users/search?q=NonexistentUserQuery")
    assert res.status_code == 200
    assert res.json()["users"] == []


@pytest.mark.asyncio
async def test_contact_lifecycle(client: AsyncClient):
    """Verify full contact lifecycle: list, add, duplicate rejection, self rejection, delete."""
    alice = await create_and_verify_user(client, "+15552000001", "Alice Contact")

    await client.post("/api/v1/auth/logout")
    bob = await create_and_verify_user(client, "+15552000002", "Bob Contact")

    # 1. Reject adding self as contact -> 400 Bad Request
    res_self = await client.post("/api/v1/contacts", json={"contact_user_id": bob["id"]})
    assert res_self.status_code == 400
    assert "yourself" in res_self.json()["detail"]

    # Login back as Alice
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    # 2. Reject non-existent target user -> 404 Not Found
    res_invalid = await client.post(
        "/api/v1/contacts", json={"contact_user_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert res_invalid.status_code == 404

    # 3. Add Bob as contact -> 201 Created
    res_add = await client.post("/api/v1/contacts", json={"contact_user_id": bob["id"]})
    assert res_add.status_code == 201
    contact_data = res_add.json()
    assert contact_data["user"]["id"] == bob["id"]
    contact_id = contact_data["id"]

    # 4. Duplicate add contact -> 409 Conflict
    res_dup = await client.post("/api/v1/contacts", json={"contact_user_id": bob["id"]})
    assert res_dup.status_code == 409

    # 5. List contacts -> 200 OK (contains 1 contact)
    res_list = await client.get("/api/v1/contacts")
    assert res_list.status_code == 200
    contacts = res_list.json()["contacts"]
    assert len(contacts) == 1
    assert contacts[0]["id"] == contact_id
    assert contacts[0]["user"]["id"] == bob["id"]

    # 6. Delete contact as non-owner (Bob trying to delete Alice's contact ID) -> 404 / 403
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": bob["phone_number"], "otp": "123456"}
    )

    res_del_non_owner = await client.delete(f"/api/v1/contacts/{contact_id}")
    assert res_del_non_owner.status_code == 404

    # 7. Delete contact as owner (Alice) -> 204 No Content
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    res_del_owner = await client.delete(f"/api/v1/contacts/{contact_id}")
    assert res_del_owner.status_code == 204

    # 8. List contacts after deletion -> empty list
    res_list_after = await client.get("/api/v1/contacts")
    assert res_list_after.status_code == 200
    assert res_list_after.json()["contacts"] == []
