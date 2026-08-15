"""Seed script for populating realistic, deterministic demo data into the Signal Clone database.

Run via:
    python -m app.seed
"""

import asyncio
import logging

from sqlalchemy import select

from app.database import async_session_factory, init_db
from app.models.contact import Contact
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.message_receipt import MessageReceipt
from app.models.participant import ConversationParticipant
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.seed")


async def seed_data():
    """Idempotently seed demo users, contacts, 1-to-1 conversations, group conversation, messages, and receipts."""
    logger.info("Initializing database schema...")
    await init_db()

    async with async_session_factory() as db:
        logger.info("Seeding users...")
        users_data = [
            {"phone_number": "+15551111111", "display_name": "Alice Smith"},
            {"phone_number": "+15552222222", "display_name": "Bob Johnson"},
            {"phone_number": "+15553333333", "display_name": "Charlie Davis"},
            {"phone_number": "+15554444444", "display_name": "David Miller"},
            {"phone_number": "+15555555555", "display_name": "Eva Wilson"},
        ]

        users: dict[str, User] = {}
        for item in users_data:
            stmt = select(User).where(User.phone_number == item["phone_number"])
            res = await db.execute(stmt)
            existing_user = res.scalar_one_or_none()
            if not existing_user:
                u = User(
                    phone_number=item["phone_number"],
                    display_name=item["display_name"],
                    is_verified=True,
                )
                db.add(u)
                await db.flush()
                users[item["phone_number"]] = u
                logger.info("Created user: %s (%s)", u.display_name, u.phone_number)
            else:
                users[item["phone_number"]] = existing_user
                logger.info(
                    "Existing user found: %s (%s)",
                    existing_user.display_name,
                    existing_user.phone_number,
                )

        alice = users["+15551111111"]
        bob = users["+15552222222"]
        charlie = users["+15553333333"]
        david = users["+15554444444"]
        eva = users["+15555555555"]

        logger.info("Seeding contacts...")
        contact_pairs = [
            (alice.id, bob.id),
            (alice.id, charlie.id),
            (alice.id, david.id),
            (alice.id, eva.id),
            (bob.id, charlie.id),
            (bob.id, david.id),
        ]
        for u_id, c_id in contact_pairs:
            stmt = select(Contact).where(
                (Contact.user_id == u_id) & (Contact.contact_user_id == c_id)
            )
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                db.add(Contact(user_id=u_id, contact_user_id=c_id))
            # Bi-directional contact insertion
            stmt_rev = select(Contact).where(
                (Contact.user_id == c_id) & (Contact.contact_user_id == u_id)
            )
            res_rev = await db.execute(stmt_rev)
            if not res_rev.scalar_one_or_none():
                db.add(Contact(user_id=c_id, contact_user_id=u_id))
        await db.flush()

        logger.info("Seeding 1-to-1 Direct Conversation (Alice <-> Bob)...")
        stmt_direct = select(Conversation).where(
            (Conversation.type == "DIRECT") & (Conversation.created_by == alice.id)
        )
        res_dir = await db.execute(stmt_direct)
        direct_conv = res_dir.scalars().first()

        if not direct_conv:
            direct_conv = Conversation(type="DIRECT", created_by=alice.id)
            db.add(direct_conv)
            await db.flush()

            db.add(
                ConversationParticipant(
                    conversation_id=direct_conv.id, user_id=alice.id, role="MEMBER"
                )
            )
            db.add(
                ConversationParticipant(
                    conversation_id=direct_conv.id, user_id=bob.id, role="MEMBER"
                )
            )
            await db.flush()

            # Seed Direct Messages
            msg1 = Message(
                conversation_id=direct_conv.id,
                sender_id=alice.id,
                content="Hey Bob! Welcome to Signal Clone.",
                message_type="TEXT",
            )
            db.add(msg1)
            await db.flush()
            db.add(MessageReceipt(message_id=msg1.id, user_id=bob.id, status="READ"))

            msg2 = Message(
                conversation_id=direct_conv.id,
                sender_id=bob.id,
                content="Hi Alice! The app is fast and responsive.",
                message_type="TEXT",
            )
            db.add(msg2)
            await db.flush()
            db.add(MessageReceipt(message_id=msg2.id, user_id=alice.id, status="READ"))

        logger.info("Seeding Group Conversation ('Engineering Team')...")
        stmt_group = select(Conversation).where(
            (Conversation.type == "GROUP") & (Conversation.name == "Engineering Team")
        )
        res_grp = await db.execute(stmt_group)
        group_conv = res_grp.scalars().first()

        if not group_conv:
            group_conv = Conversation(
                type="GROUP",
                name="Engineering Team",
                created_by=alice.id,
            )
            db.add(group_conv)
            await db.flush()

            # Add Participants (Alice = ADMIN, Bob/Charlie/David = MEMBER)
            db.add(
                ConversationParticipant(
                    conversation_id=group_conv.id, user_id=alice.id, role="ADMIN"
                )
            )
            db.add(
                ConversationParticipant(
                    conversation_id=group_conv.id, user_id=bob.id, role="MEMBER"
                )
            )
            db.add(
                ConversationParticipant(
                    conversation_id=group_conv.id, user_id=charlie.id, role="MEMBER"
                )
            )
            db.add(
                ConversationParticipant(
                    conversation_id=group_conv.id, user_id=david.id, role="MEMBER"
                )
            )
            await db.flush()

            # Seed Group Messages
            grp_msg1 = Message(
                conversation_id=group_conv.id,
                sender_id=alice.id,
                content="Welcome to the Engineering Team group chat! 🚀",
                message_type="TEXT",
            )
            db.add(grp_msg1)
            await db.flush()
            db.add(MessageReceipt(message_id=grp_msg1.id, user_id=bob.id, status="READ"))
            db.add(MessageReceipt(message_id=grp_msg1.id, user_id=charlie.id, status="READ"))
            db.add(MessageReceipt(message_id=grp_msg1.id, user_id=david.id, status="DELIVERED"))

            grp_msg2 = Message(
                conversation_id=group_conv.id,
                sender_id=bob.id,
                content="Excited to work together on this release!",
                message_type="TEXT",
            )
            db.add(grp_msg2)
            await db.flush()
            db.add(MessageReceipt(message_id=grp_msg2.id, user_id=alice.id, status="READ"))
            db.add(MessageReceipt(message_id=grp_msg2.id, user_id=charlie.id, status="DELIVERED"))
            db.add(MessageReceipt(message_id=grp_msg2.id, user_id=david.id, status="SENT"))

            grp_msg3 = Message(
                conversation_id=group_conv.id,
                sender_id=charlie.id,
                content="Group messaging and per-user receipts look great.",
                message_type="TEXT",
            )
            db.add(grp_msg3)
            await db.flush()
            db.add(MessageReceipt(message_id=grp_msg3.id, user_id=alice.id, status="READ"))
            db.add(MessageReceipt(message_id=grp_msg3.id, user_id=bob.id, status="READ"))
            db.add(MessageReceipt(message_id=grp_msg3.id, user_id=david.id, status="SENT"))

        await db.commit()
        logger.info("Successfully seeded demo data!")


if __name__ == "__main__":
    asyncio.run(seed_data())
