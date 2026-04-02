import logging
import threading

from .models import AnalyticsEvent
from .utils import hash_ip

logger = logging.getLogger(__name__)

SESSION_COOKIE = 'ehub_sid'


def _get_session_id(request):
    if request is None:
        return ''
    return request.COOKIES.get(SESSION_COOKIE, '')


def track(event_type, request=None, properties=None, user=None,
          item_id='', item_type=''):
    """비즈니스 이벤트를 비동기로 기록한다. 뷰 응답 속도에 영향을 주지 않는다."""
    ip = hash_ip(request) if request else ''
    session_id = _get_session_id(request)

    if user is None and request and hasattr(request, 'user'):
        u = request.user
        if u and u.is_authenticated:
            user = u

    _item_id = str(item_id) if item_id else ''
    _item_type = str(item_type) if item_type else ''

    def _save():
        try:
            AnalyticsEvent.objects.create(
                event_type=event_type,
                properties=properties or {},
                ip_hash=ip,
                user=user,
                item_id=_item_id,
                item_type=_item_type,
                session_id=session_id,
            )
        except Exception:
            logger.warning('Failed to save analytics event', extra={
                'event_type': event_type,
            })

    threading.Thread(target=_save, daemon=True).start()
