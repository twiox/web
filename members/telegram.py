"""Short notifications to Telegram groups via a bot (Bot API sendMessage).

The bot token is the only setting (TELEGRAM_BOT_TOKEN, from @BotFather); without it nothing is sent,
e.g. in local development. Where a notification goes is maintained in the admin as TelegramTarget:
the code only names the target ("trainers", "board", …), unknown or inactive targets are skipped.

Messages go through Telegram's servers: keep them short and without personal data, link to the site instead.
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

from .models import TelegramTarget

logger = logging.getLogger(__name__)


def notify_telegram(text, target):
    """Send text to the named target; failures are only logged, they never break the page. Returns True if sent."""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not token:
        return False
    destination = TelegramTarget.objects.filter(name=target, active=True).first()
    if destination is None:
        return False  # not set up (yet) or switched off in the admin
    payload = {"chat_id": destination.chat_id, "text": text, "disable_web_page_preview": True}
    if destination.topic_id:
        payload["message_thread_id"] = destination.topic_id
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.load(response).get("ok", False)
    except urllib.error.HTTPError as error:
        # Telegram explains the problem in the body, e.g. "Bad Request: chat not found"
        logger.error("Telegram notification to %s failed: %s %s", target, error.code, error.read().decode(errors="replace"))
        return False
    except Exception:
        logger.exception("Telegram notification to %s failed", target)
        return False
