from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .analytics import track

ALLOWED_EVENT_TYPES = frozenset({
    'page_view',
    'outbound_click',
    'share',
    'tool_use',
    'calendar_view',
})

MAX_PROPERTIES_SIZE = 20


class EventTrackView(APIView):
    """POST /api/v1/events/ — 프론트엔드 이벤트를 AnalyticsEvent 테이블에 기록한다."""

    def post(self, request):
        events = request.data if isinstance(request.data, list) else [request.data]

        if len(events) > 10:
            return Response(
                {'error': 'Maximum 10 events per request.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        saved = 0
        for event in events:
            event_type = event.get('event_type') or event.get('eventType')
            if not event_type or event_type not in ALLOWED_EVENT_TYPES:
                continue

            properties = event.get('properties', {})
            if not isinstance(properties, dict) or len(properties) > MAX_PROPERTIES_SIZE:
                continue

            track(event_type, request, properties)
            saved += 1

        return Response({'saved': saved}, status=status.HTTP_202_ACCEPTED)
