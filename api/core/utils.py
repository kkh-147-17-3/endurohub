import hashlib
import re

from django.conf import settings
from django.core.cache import cache
from django.db.models import IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import HttpRequest

# 검색엔진/AI 크롤러 User-Agent 패턴. 'bot'은 bingbot/Googlebot/ClaudeBot/
# GPTBot/AhrefsBot/SemrushBot/PetalBot/DuckDuckBot 등을 한 번에 잡는다.
_BOT_UA_RE = re.compile(
    r'bot|crawl|spider|slurp|yeti|daum|facebookexternalhit|mediapartners|'
    r'embedly|bingpreview|google web preview|archive\.org|headlesschrome',
    re.IGNORECASE,
)


def is_bot_request(request: HttpRequest | None) -> bool:
    """크롤러/봇 요청이면 True. SSR이 포워딩한 원본 UA를 우선 확인한다."""
    if request is None:
        return False
    ua = (
        request.META.get('HTTP_X_FORWARDED_USER_AGENT', '')
        or request.META.get('HTTP_USER_AGENT', '')
    )
    return bool(ua) and bool(_BOT_UA_RE.search(ua))


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP from X-Forwarded-For header."""
    x_forwarded_for: str | None = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    remote_addr: str = request.META.get('REMOTE_ADDR', 'unknown')
    return remote_addr


def hash_ip(request: HttpRequest) -> str:
    """Hash client IP with SECRET_KEY using SHA256."""
    ip = get_client_ip(request)
    return hashlib.sha256(f"{ip}{settings.SECRET_KEY}".encode()).hexdigest()


def post_count_subqueries() -> tuple[Coalesce, Coalesce]:
    """
    Return Subquery annotations for Post comment_count and like_count.
    Uses Subquery instead of Count to avoid GROUP BY issues with json columns.
    """
    from django.db.models import Count as DjangoCount

    from posts.models import PostComment, PostLike

    comment_count = Coalesce(
        Subquery(
            PostComment.objects.filter(post_id=OuterRef('pk'))
            .order_by()
            .values('post_id')
            .annotate(c=DjangoCount('id'))
            .values('c'),
            output_field=IntegerField(),
        ),
        Value(0),
    )
    like_count = Coalesce(
        Subquery(
            PostLike.objects.filter(post_id=OuterRef('pk'))
            .order_by()
            .values('post_id')
            .annotate(c=DjangoCount('id'))
            .values('c'),
            output_field=IntegerField(),
        ),
        Value(0),
    )
    return comment_count, like_count


def check_rate_limit(ip_hash: str, action: str, max_attempts: int, window_seconds: int) -> tuple[bool, int]:
    """
    Check and increment rate limit counter.
    Returns (allowed: bool, remaining: int).
    """
    cache_key = f'{action}_rate_limit:{ip_hash}'
    current = cache.get(cache_key, 0)
    if current >= max_attempts:
        return False, 0
    cache.set(cache_key, current + 1, window_seconds)
    return True, max_attempts - current - 1
