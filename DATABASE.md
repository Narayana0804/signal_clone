# DATABASE.md — Signal Clone

## Design Philosophy

- **Unified Conversation Model**: One `conversations` table handles both DIRECT and GROUP types. Avoids duplicating messaging logic.
- **Per-User Receipts**: `message_receipts` tracks DELIVERED/READ state per recipient, enabling accurate group receipt display.
- **Explicit Relationships**: All foreign keys enforced. No orphan records. CASCADE deletes where appropriate.
- **SQLite Compatibility**: All types, constraints, and indexes are SQLite-compatible. UUIDs stored as TEXT. Timestamps stored as TEXT (ISO 8601).

## Entity-Relationship Diagram

```
┌──────────────┐       ┌───────────────┐       ┌──────────────────────┐
│    users     │       │   sessions    │       │      contacts        │
├──────────────┤       ├───────────────┤       ├──────────────────────┤
│ id (PK)      │──┐    │ id (PK)       │       │ id (PK)              │
│ phone_number │  │    │ user_id (FK)──┼──►    │ user_id (FK)────────►│
│ display_name │  │    │ token_hash    │       │ contact_user_id (FK)►│
│ avatar_url   │  │    │ expires_at    │       │ created_at           │
│ about        │  │    │ created_at    │       └──────────────────────┘
│ created_at   │  │    └───────────────┘
│ updated_at   │  │
│ last_seen_at │  │
└──────────────┘  │
                  │
        ┌─────────┘
        │
        ▼
┌───────────────────────────┐       ┌──────────────────────────────────┐
│   conversation_participants│       │        conversations             │
├───────────────────────────┤       ├──────────────────────────────────┤
│ id (PK)                   │       │ id (PK)                          │
│ conversation_id (FK)──────┼──────►│ type (DIRECT/GROUP)              │
│ user_id (FK)──────────────┼──►    │ name (NULL for DIRECT)           │
│ role (MEMBER/ADMIN)       │       │ avatar_url                       │
│ joined_at                 │       │ created_by (FK)──────────────────►│
│ left_at (NULL=active)     │       │ created_at                       │
│ last_read_message_id (FK) │       │ updated_at                       │
└───────────────────────────┘       └──────────────────────────────────┘
                                              │
                                              ▼
                                    ┌──────────────────────┐
                                    │      messages        │
                                    ├──────────────────────┤
                                    │ id (PK)              │
                                    │ conversation_id (FK) │
                                    │ sender_id (FK)       │
                                    │ content              │
                                    │ message_type (TEXT)   │
                                    │ reply_to_id (FK,NULL) │
                                    │ created_at           │
                                    │ updated_at           │
                                    │ deleted_at (NULL)    │
                                    └──────────────────────┘
                                              │
                                              ▼
                                    ┌──────────────────────┐
                                    │  message_receipts    │
                                    ├──────────────────────┤
                                    │ id (PK)              │
                                    │ message_id (FK)      │
                                    │ user_id (FK)         │
                                    │ status (SENT/        │
                                    │   DELIVERED/READ)    │
                                    │ delivered_at (NULL)  │
                                    │ read_at (NULL)       │
                                    └──────────────────────┘
```

## Table Definitions

### `users`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | TEXT | PK, UUID | Generated UUID v4 |
| `phone_number` | TEXT | UNIQUE, NOT NULL | Format: `+1234567890` |
| `display_name` | TEXT | NOT NULL | User-chosen display name |
| `avatar_url` | TEXT | NULL | URL or path to avatar image |
| `about` | TEXT | NULL, DEFAULT '' | Status/about text |
| `is_verified` | INTEGER | NOT NULL, DEFAULT 0 | 0=unverified, 1=verified |
| `created_at` | TEXT | NOT NULL, DEFAULT NOW | ISO 8601 |
| `updated_at` | TEXT | NOT NULL, DEFAULT NOW | ISO 8601 |
| `last_seen_at` | TEXT | NULL | Last online timestamp |

**Indexes:**
- `ix_users_phone_number` on `phone_number` (unique)
- `ix_users_display_name` on `display_name` (for search)

---

### `sessions`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | TEXT | PK, UUID | Session identifier |
| `user_id` | TEXT | FK → users.id, NOT NULL | Session owner |
| `token_hash` | TEXT | UNIQUE, NOT NULL | SHA-256 hash of raw token |
| `expires_at` | TEXT | NOT NULL | Expiration timestamp |
| `created_at` | TEXT | NOT NULL, DEFAULT NOW | Creation timestamp |

**Indexes:**
- `ix_sessions_token_hash` on `token_hash` (unique, for lookup)
- `ix_sessions_user_id` on `user_id`

**Cascade:** DELETE user → DELETE sessions

---

### `contacts`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | TEXT | PK, UUID | |
| `user_id` | TEXT | FK → users.id, NOT NULL | The user who added the contact |
| `contact_user_id` | TEXT | FK → users.id, NOT NULL | The contact being added |
| `created_at` | TEXT | NOT NULL, DEFAULT NOW | |

**Constraints:**
- UNIQUE(`user_id`, `contact_user_id`) — cannot add same contact twice
- CHECK(`user_id != contact_user_id`) — cannot add self as contact

**Indexes:**
- `ix_contacts_user_id` on `user_id`
- `uq_contacts_pair` on (`user_id`, `contact_user_id`) (unique)

**Cascade:** DELETE user → DELETE contacts (both directions)

---

### `conversations`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | TEXT | PK, UUID | |
| `type` | TEXT | NOT NULL, CHECK IN ('DIRECT','GROUP') | Conversation type |
| `name` | TEXT | NULL | NULL for DIRECT; required for GROUP |
| `avatar_url` | TEXT | NULL | Group avatar |
| `created_by` | TEXT | FK → users.id, NOT NULL | Creator |
| `created_at` | TEXT | NOT NULL, DEFAULT NOW | |
| `updated_at` | TEXT | NOT NULL, DEFAULT NOW | Updated on new messages |

**Indexes:**
- `ix_conversations_type` on `type`
- `ix_conversations_updated_at` on `updated_at` (for ordering)

---

### `conversation_participants`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | TEXT | PK, UUID | |
| `conversation_id` | TEXT | FK → conversations.id, NOT NULL | |
| `user_id` | TEXT | FK → users.id, NOT NULL | |
| `role` | TEXT | NOT NULL, DEFAULT 'MEMBER', CHECK IN ('ADMIN','MEMBER') | |
| `joined_at` | TEXT | NOT NULL, DEFAULT NOW | |
| `left_at` | TEXT | NULL | NULL = active participant |
| `last_read_message_id` | TEXT | FK → messages.id, NULL, ON DELETE SET NULL | Last message this user has read |

**Constraints:**
- UNIQUE(`conversation_id`, `user_id`) — user can only be in a conversation once

**Indexes:**
- `ix_cp_conversation_id` on `conversation_id`
- `ix_cp_user_id` on `user_id`
- `uq_cp_conv_user` on (`conversation_id`, `user_id`) (unique)

**Cascade:** DELETE conversation → DELETE participants

**Invariants:**
- A DIRECT conversation must have exactly 2 participants
- A GROUP conversation must have at least 1 participant with role ADMIN
- There should be at most 1 DIRECT conversation between any pair of users

---

### `messages`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | TEXT | PK, UUID | |
| `conversation_id` | TEXT | FK → conversations.id, NOT NULL | |
| `sender_id` | TEXT | FK → users.id, NOT NULL | Must be a participant |
| `content` | TEXT | NOT NULL | Message text |
| `message_type` | TEXT | NOT NULL, DEFAULT 'TEXT', CHECK IN ('TEXT','SYSTEM') | |
| `reply_to_id` | TEXT | FK → messages.id, NULL | For reply-to (P2 bonus) |
| `created_at` | TEXT | NOT NULL, DEFAULT NOW | Message timestamp |
| `updated_at` | TEXT | NULL | Edit timestamp |
| `deleted_at` | TEXT | NULL | Soft delete timestamp |

**Indexes:**
- `ix_messages_conversation_id` on `conversation_id`
- `ix_messages_conversation_created` on (`conversation_id`, `created_at`) — primary query pattern
- `ix_messages_sender_id` on `sender_id`

**Cascade:** DELETE conversation → DELETE messages

**Invariants:**
- `sender_id` must reference a user who is (or was) a participant in `conversation_id`
- Messages are never hard-deleted; use `deleted_at` for soft deletion

---

### `message_receipts`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | TEXT | PK, UUID | |
| `message_id` | TEXT | FK → messages.id, NOT NULL | |
| `user_id` | TEXT | FK → users.id, NOT NULL | Recipient |
| `status` | TEXT | NOT NULL, DEFAULT 'SENT', CHECK IN ('SENT','DELIVERED','READ') | |
| `delivered_at` | TEXT | NULL | When DELIVERED |
| `read_at` | TEXT | NULL | When READ |

**Constraints:**
- UNIQUE(`message_id`, `user_id`) — one receipt per user per message

**Indexes:**
- `ix_mr_message_id` on `message_id`
- `ix_mr_user_id` on `user_id`
- `uq_mr_message_user` on (`message_id`, `user_id`) (unique)

**Cascade:** DELETE message → DELETE receipts

**Invariants:**
- Receipt `user_id` must NOT be the `sender_id` of the message (sender doesn't receive their own message)
- Receipt `user_id` must be a participant in the message's conversation
- Status transitions: SENT → DELIVERED → READ (never backwards)

---

## Unread Count Strategy

Unread count for a user in a conversation is computed as:

```sql
SELECT COUNT(*)
FROM messages m
WHERE m.conversation_id = :conv_id
  AND m.sender_id != :user_id
  AND m.deleted_at IS NULL
  AND m.created_at > COALESCE(
    (SELECT m2.created_at FROM messages m2 WHERE m2.id = :last_read_message_id),
    '1970-01-01T00:00:00Z'
  )
```

This uses the `last_read_message_id` from `conversation_participants` to determine the read watermark, then counts messages after that point.

**Why `last_read_message_id` instead of receipt-based count:**
- More efficient: single comparison vs. LEFT JOIN on receipts
- Simpler: conversation list only needs the watermark
- Receipts are still used for per-message status display in the chat view

## Last Message Preview Strategy

For the conversation list, we need the last message per conversation:

```sql
SELECT c.*, m.content as last_message_content, m.created_at as last_message_at, m.sender_id as last_message_sender_id
FROM conversations c
JOIN conversation_participants cp ON cp.conversation_id = c.id AND cp.user_id = :user_id AND cp.left_at IS NULL
LEFT JOIN messages m ON m.id = (
  SELECT m2.id FROM messages m2
  WHERE m2.conversation_id = c.id AND m2.deleted_at IS NULL
  ORDER BY m2.created_at DESC LIMIT 1
)
ORDER BY COALESCE(m.created_at, c.created_at) DESC
```

## Key Design Decisions

### Why UUID for Primary Keys
- Allows client-generated IDs (useful for optimistic updates)
- No sequential ID enumeration vulnerability
- Works well across distributed scenarios (future-proofing, though not required now)

### Why TEXT for Timestamps (ISO 8601)
- SQLite has no native datetime type
- TEXT with ISO 8601 is sortable, human-readable, and unambiguous
- Stored as UTC

### Why `last_read_message_id` on `conversation_participants`
- Enables O(1) unread watermark lookup per conversation
- Avoids expensive receipt-based aggregation for conversation list
- Updated atomically when user reads messages

### Why Separate `message_receipts` Table
- Per-user receipt state is required for groups
- Enables showing "delivered to 3, read by 2" in group chats
- Receipts are created for all non-sender participants when a message is sent (initial status: SENT)

### Why Soft Delete for Messages
- Maintains referential integrity (replies, receipts)
- Allows "This message was deleted" UI pattern
- Reversible

## Migration Strategy

Using Alembic for schema migrations:
- Initial migration creates all tables
- Seed data is applied via a separate `seed.py` script (not a migration)
- Migrations tracked in `alembic/versions/`
