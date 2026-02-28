import json
import logging
import traceback
import urllib.request
import urllib.error
from threading import Thread

from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram(message):
    """Telegram Bot API로 메시지를 전송한다. 별도 스레드에서 비동기 실행."""
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', '')

    if not bot_token or not chat_id:
        return

    def _send():
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        # Telegram 메시지 최대 4096자
        truncated = message[:4000]
        payload = json.dumps({
            'chat_id': chat_id,
            'text': truncated,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True,
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        try:
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            logger.warning('Telegram 알림 전송 실패', exc_info=True)

    Thread(target=_send, daemon=True).start()


def notify_server_error(request, exception):
    """500 에러 발생 시 Telegram으로 알림을 보낸다."""
    method = request.method
    path = request.get_full_path()
    exc_type = type(exception).__name__
    exc_msg = str(exception)
    tb = traceback.format_exc()

    # 트레이스백은 마지막 1500자만
    if len(tb) > 1500:
        tb = '...\n' + tb[-1500:]

    message = (
        f'<b>500 Server Error</b>\n'
        f'<b>Method:</b> {method}\n'
        f'<b>Path:</b> <code>{path}</code>\n'
        f'<b>Exception:</b> {exc_type}: {exc_msg}\n\n'
        f'<pre>{tb}</pre>'
    )

    send_telegram(message)
