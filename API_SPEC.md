# API_SPEC.md — Signal Clone

## Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://<backend-domain>/api/v1
```

## Common Conventions

- **Content-Type**: `application/json`
- **Authentication**: HTTP-only cookie `session_token` for REST; query parameter `token` for WebSocket
- **IDs**: UUID v4 (string format)
- **Timestamps**: ISO 8601 UTC (e.g., `2024-01-15T10:30:00Z`)
- **Pagination**: Cursor-based using `before` (message ID) + `limit` (default 50)
- **Errors**: Consistent JSON error format

## Error Response Format

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE",
  "field": "optional_field_name"
}
```

Common HTTP status codes:
| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request (validation) |
| 401 | Unauthorized (no/invalid session) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 422 | Unprocessable Entity (Pydantic validation) |
| 500 | Internal Server Error |

---

## Health

### `GET /health`

No authentication required.

**Response 200:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Authentication

### `POST /api/v1/auth/register`

Register a new user. If phone number already exists, returns 409.

**Request:**
```json
{
  "phone_number": "+1234567890",
  "display_name": "Alice"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "phone_number": "+1234567890",
  "display_name": "Alice",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:** 409 Conflict (phone already registered), 422 Validation

---

### `POST /api/v1/auth/verify`

Verify phone number with OTP. Always accepts `123456`.

**Request:**
```json
{
  "phone_number": "+1234567890",
  "otp": "123456"
}
```

**Response 200:**
```json
{
  "verified": true
}
```

**Errors:** 400 Invalid OTP, 404 User not found

---

### `POST /api/v1/auth/login`

Login and receive session cookie. User must be verified first.

**Request:**
```json
{
  "phone_number": "+1234567890",
  "otp": "123456"
}
```

**Response 200:**
```json
{
  "user": {
    "id": "uuid",
    "phone_number": "+1234567890",
    "display_name": "Alice",
    "avatar_url": null,
    "about": "",
    "is_verified": 1,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

Sets `Set-Cookie: session_token=<token>; HttpOnly; Path=/; SameSite=Lax (dev) / None (prod); Secure (prod)`

> [!NOTE]
> Authentication is strictly governed by the HTTP-only session cookie. The raw session token is NOT returned in the response body to prevent credential leakage to JavaScript state.

> [!NOTE]
> Mock OTP: Fixed code `123456` is used for phone verification per assignment scope. No real SMS provider is connected.

**Errors:** 400 Unverified user / Invalid OTP, 404 User not found

---

### `POST /api/v1/auth/logout`

Invalidate current session.

**Request:** No body. Uses cookie.

**Response 200:**
```json
{
  "message": "Logged out"
}
```

Clears the session cookie.

---

### `GET /api/v1/auth/me`

Get current authenticated user.

**Response 200:**
```json
{
  "id": "uuid",
  "phone_number": "+1234567890",
  "display_name": "Alice",
  "avatar_url": null,
  "about": "",
  "created_at": "2024-01-15T10:30:00Z",
  "last_seen_at": "2024-01-15T10:30:00Z"
}
```

**Errors:** 401 Unauthorized

---

### `PATCH /api/v1/auth/me`

Update current user profile.

**Request:**
```json
{
  "display_name": "Alice Smith",
  "about": "Available"
}
```

**Response 200:** Updated user object.

---

## Users

### `GET /api/v1/users/search?q={query}`

Search users by display name or phone number. Excludes current user.

**Query Parameters:**
- `q` (required): Search query (min 2 chars)
- `limit` (optional): Max results (default 20)

**Response 200:**
```json
{
  "users": [
    {
      "id": "uuid",
      "phone_number": "+1234567890",
      "display_name": "Bob",
      "avatar_url": null,
      "about": ""
    }
  ]
}
```

---

## Contacts

### `GET /api/v1/contacts`

List current user's contacts.

**Response 200:**
```json
{
  "contacts": [
    {
      "id": "contact_uuid",
      "user": {
        "id": "user_uuid",
        "phone_number": "+1234567890",
        "display_name": "Bob",
        "avatar_url": null,
        "about": ""
      },
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### `POST /api/v1/contacts`

Add a contact.

**Request:**
```json
{
  "contact_user_id": "uuid"
}
```

**Response 201:**
```json
{
  "id": "contact_uuid",
  "user": { ... },
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:** 404 User not found, 409 Already a contact, 400 Cannot add self

---

### `DELETE /api/v1/contacts/{contact_id}`

Remove a contact.

**Response 204:** No content.

**Errors:** 404 Contact not found

---

## Conversations

### `GET /api/v1/conversations`

List conversations for the current user, ordered by most recent activity.

**Query Parameters:**
- `search` (optional): Filter by conversation name or participant name

**Response 200:**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "type": "DIRECT",
      "name": null,
      "avatar_url": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:00:00Z",
      "last_message": {
        "id": "msg_uuid",
        "content": "Hey there!",
        "sender_id": "user_uuid",
        "sender_name": "Bob",
        "created_at": "2024-01-15T11:00:00Z",
        "message_type": "TEXT"
      },
      "unread_count": 3,
      "participants": [
        {
          "id": "participant_uuid",
          "user_id": "user_uuid",
          "display_name": "Bob",
          "avatar_url": null,
          "role": "MEMBER"
        }
      ],
      "other_user": {
        "id": "user_uuid",
        "display_name": "Bob",
        "avatar_url": null,
        "phone_number": "+1234567890"
      }
    }
  ]
}
```

Note: `other_user` is populated only for DIRECT conversations (convenience for UI).

---

### `POST /api/v1/conversations`

Create a new conversation.

**Request (Direct):**
```json
{
  "type": "DIRECT",
  "participant_ids": ["other_user_uuid"]
}
```

**Request (Group):**
```json
{
  "type": "GROUP",
  "name": "Project Team",
  "participant_ids": ["user_uuid_1", "user_uuid_2"]
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "type": "GROUP",
  "name": "Project Team",
  "participants": [ ... ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

For DIRECT: if a conversation already exists between the two users, returns the existing one (200).

**Errors:** 400 Invalid participants, 400 Group name required

---

### `GET /api/v1/conversations/{id}`

Get conversation details.

**Response 200:** Full conversation object with participants.

**Errors:** 403 Not a participant, 404 Not found

---

### `PATCH /api/v1/conversations/{id}`

Update group conversation (name, avatar). Admin only for groups.

**Request:**
```json
{
  "name": "New Group Name"
}
```

**Response 200:** Updated conversation.

**Errors:** 403 Not admin

---

## Messages

### `GET /api/v1/conversations/{conversation_id}/messages`

Get messages for a conversation. Cursor-based pagination.

**Query Parameters:**
- `before` (optional): Message ID — get messages before this one
- `limit` (optional): Max messages (default 50, max 100)

**Response 200:**
```json
{
  "messages": [
    {
      "id": "uuid",
      "conversation_id": "conv_uuid",
      "sender_id": "user_uuid",
      "sender": {
        "id": "user_uuid",
        "display_name": "Alice",
        "avatar_url": null
      },
      "content": "Hello!",
      "message_type": "TEXT",
      "reply_to_id": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": null,
      "deleted_at": null,
      "receipts": [
        {
          "user_id": "user_uuid",
          "status": "READ",
          "delivered_at": "2024-01-15T10:30:05Z",
          "read_at": "2024-01-15T10:31:00Z"
        }
      ]
    }
  ],
  "has_more": true
}
```

**Errors:** 403 Not a participant

---

### `POST /api/v1/conversations/{conversation_id}/messages`

Send a message to a conversation.

**Request:**
```json
{
  "content": "Hello!",
  "message_type": "TEXT",
  "client_id": "client_generated_uuid"
}
```

`client_id` is a client-generated UUID for idempotency and optimistic update matching.

**Response 201:**
```json
{
  "id": "server_uuid",
  "client_id": "client_generated_uuid",
  "conversation_id": "conv_uuid",
  "sender_id": "user_uuid",
  "content": "Hello!",
  "message_type": "TEXT",
  "created_at": "2024-01-15T10:30:00Z",
  "receipts": [ ... ]
}
```

**Side effects:**
- Creates `message_receipts` for all other active participants (status: SENT)
- Broadcasts `message.created` via WebSocket
- Updates `conversations.updated_at`

**Errors:** 403 Not a participant, 400 Empty content

---

### `POST /api/v1/messages/{message_id}/read`

Mark a message (and all prior messages) as read.

**Request:** No body.

**Response 200:**
```json
{
  "read_count": 5
}
```

**Side effects:**
- Updates `conversation_participants.last_read_message_id`
- Updates `message_receipts.status` to READ for all messages up to this one
- Broadcasts `message.read` via WebSocket to message senders

**Errors:** 403 Not a participant

---

## Conversation Members (Groups)

### `GET /api/v1/conversations/{id}/members`

List members of a conversation.

**Response 200:**
```json
{
  "members": [
    {
      "id": "participant_uuid",
      "user": {
        "id": "user_uuid",
        "display_name": "Alice",
        "avatar_url": null,
        "phone_number": "+1234567890"
      },
      "role": "ADMIN",
      "joined_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### `POST /api/v1/conversations/{id}/members`

Add members to a group. Admin only.

**Request:**
```json
{
  "user_ids": ["uuid1", "uuid2"]
}
```

**Response 201:**
```json
{
  "added": ["uuid1", "uuid2"]
}
```

**Side effects:**
- Creates SYSTEM message ("Alice added Bob")
- Broadcasts `participant.added` via WebSocket

**Errors:** 403 Not admin, 400 Not a group, 409 Already a member

---

### `DELETE /api/v1/conversations/{id}/members/{user_id}`

Remove a member from a group. Admin only. Cannot remove last admin.

**Response 204:** No content.

**Side effects:**
- Sets `left_at` on participant record
- Creates SYSTEM message ("Alice removed Bob")
- Broadcasts `participant.removed` via WebSocket

**Errors:** 403 Not admin, 400 Cannot remove last admin

---

### `PATCH /api/v1/conversations/{id}/members/{user_id}`

Update member role. Admin only.

**Request:**
```json
{
  "role": "ADMIN"
}
```

**Response 200:** Updated member.

**Side effects:**
- Creates SYSTEM message ("Alice made Bob an admin")
- Broadcasts `participant.role_changed` via WebSocket

**Errors:** 403 Not admin, 400 Cannot demote last admin
