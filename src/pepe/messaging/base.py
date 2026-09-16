"""Messaging abstraction. The agent never cares which channel a message came from."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class NormalizedMessage:
    channel: str  # telegram | whatsapp | slack | teams | web
    user_id: str
    deal_id: str | None
    content: str
    attachments: list[str] = field(default_factory=list)


class MessageChannel(Protocol):
    name: str

    def send(self, user_id: str, text: str) -> None:
        ...

    def receive(self) -> NormalizedMessage:
        ...


class TelegramAdapter:
    """Phase 2: python-telegram-bot polling. Phase 0: stub."""

    name = "telegram"

    def __init__(self, token: str = "") -> None:
        self.token = token

    def send(self, user_id: str, text: str) -> None:
        raise NotImplementedError

    def receive(self) -> NormalizedMessage:
        raise NotImplementedError


class WhatsAppAdapter:
    """Phase 2+: webhook adapter. Phase 0: stub."""

    name = "whatsapp"

    def send(self, user_id: str, text: str) -> None:
        raise NotImplementedError

    def receive(self) -> NormalizedMessage:
        raise NotImplementedError
