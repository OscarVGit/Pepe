# MESSAGING — Adapter, Not Agent

`MessageChannel` Protocol (`messaging/base.py`): `send(user_id, text)` /
`receive() → NormalizedMessage(channel, user_id, deal_id, content, attachments)`.
The runtime only sees normalized messages.

Telegram first (polling, `python-telegram-bot`, no public URL needed for dev);
WhatsApp second (webhook, 24h window constraints); Slack (socket mode) /
Teams / Web later. Auth: challenge/allowlist of user IDs; every inbound message
bound to user + deal; async replies + status updates supported.

Example: Telegram "Pepe, check Atlas EBITDA." → normalized task (deal Atlas,
user Oscar) → tools (CIM/Excel/Python) → Telegram reply with $1.8m discrepancy
breakdown + approval question for the remaining $600k.
