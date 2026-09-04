from datetime import datetime

from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import RaceRecord
from races.models import Review


class CoffeeCouponEventStatusView(APIView):
    """현재 회원의 커피 쿠폰 이벤트 참여 조건 완료 여부."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tz = timezone.get_current_timezone()
        starts_at = timezone.make_aware(datetime(2026, 9, 3), tz)
        ends_at = timezone.make_aware(datetime(2026, 10, 1), tz)

        reviews = Review.objects.filter(
            user=request.user,
            created_at__gte=starts_at,
            created_at__lt=ends_at,
        )
        records = RaceRecord.objects.filter(
            user=request.user,
            race_id__in=reviews.values('race_id'),
        ).filter(
            Q(created_at__gte=starts_at, created_at__lt=ends_at)
            | Q(updated_at__gte=starts_at, updated_at__lt=ends_at)
        )

        review_count = reviews.count()
        record_count = records.count()

        return Response({
            'period': {
                'starts_at': starts_at,
                'ends_at': ends_at,
            },
            'review': {
                'completed': review_count > 0,
                'count': review_count,
            },
            'record': {
                'completed': record_count > 0,
                'count': record_count,
            },
            'completed': review_count > 0 and record_count > 0,
        })
