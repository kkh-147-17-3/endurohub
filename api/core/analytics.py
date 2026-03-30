import logging
import threading

from .models import AnalyticsEvent
from .utils import hash_ip

logger = logging.getLogger(__name__)


def track(event_type, request=None, properties=None, user=None):
    """비즈니스 이벤트를 비동기로 기록한다. 뷰 응답 속도에 영향을 주지 않는다."""
    ip = hash_ip(request) if request else ''
    if user is None and request and hasattr(request, 'user'):
        u = request.user
        if u and u.is_authenticated:
            user = u

    def _save():
        try:
            AnalyticsEvent.objects.create(
                event_type=event_type,
                properties=properties or {},
                ip_hash=ip,
                user=user,
            )
        except Exception:
            logger.warning('Failed to save analytics event', extra={
                'event_type': event_type,
            })

    threading.Thread(target=_save, daemon=True).start()
