"""Admin dashboard template tags.

Renders a "registered user × day" analytics-event matrix on the unfold
admin home (`/dj-admin/`). Kept as an inclusion tag so it works with the
default admin site without swapping in UnfoldAdminSite.
"""
from datetime import timedelta

from django import template
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone

from core.models import AnalyticsEvent

register = template.Library()

WINDOW_DAYS = 14
ACCENT = (67, 165, 100)  # #43a564


def _cell(count, max_count):
    """Build a heatmap cell (count + background color)."""
    if not count:
        return {'count': 0, 'bg': 'transparent', 'fg': '#9ca3af'}
    ratio = count / max_count if max_count else 0
    alpha = round(0.12 + 0.78 * ratio, 3)
    r, g, b = ACCENT
    return {
        'count': count,
        'bg': f'rgba({r},{g},{b},{alpha})',
        'fg': '#ffffff' if ratio > 0.55 else '#14532d',
    }


@register.inclusion_tag('admin/analytics_user_matrix.html')
def analytics_user_matrix():
    tz = timezone.get_current_timezone()
    today = timezone.localdate()
    start_date = today - timedelta(days=WINDOW_DAYS - 1)
    days = [start_date + timedelta(days=i) for i in range(WINDOW_DAYS)]

    # Events per (registered user, local day) within the window.
    agg = (
        AnalyticsEvent.objects
        .filter(user__isnull=False, created_at__date__gte=start_date)
        .annotate(day=TruncDate('created_at', tzinfo=tz))
        .values('user_id', 'day')
        .annotate(c=Count('id'))
    )

    counts = {}   # user_id -> {day: count}
    totals = {}   # user_id -> total
    max_count = 0
    for r in agg:
        counts.setdefault(r['user_id'], {})[r['day']] = r['c']
        totals[r['user_id']] = totals.get(r['user_id'], 0) + r['c']
        if r['c'] > max_count:
            max_count = r['c']

    User = get_user_model()
    user_labels = {}
    for u in User.objects.filter(pk__in=counts.keys()):
        user_labels[u.pk] = u.email or u.get_username() or f'user#{u.pk}'

    rows = []
    for uid in sorted(counts, key=lambda k: totals.get(k, 0), reverse=True):
        try:
            change_url = reverse('admin:auth_user_change', args=[uid])
        except Exception:
            change_url = ''
        rows.append({
            'label': user_labels.get(uid, f'user#{uid}'),
            'url': change_url,
            'cells': [_cell(counts[uid].get(d, 0), max_count) for d in days],
            'total': totals[uid],
        })

    col_totals = [sum(counts.get(uid, {}).get(d, 0) for uid in counts) for d in days]

    return {
        'days': days,
        'rows': rows,
        'col_totals': col_totals,
        'grand_total': sum(totals.values()),
        'user_count': len(rows),
        'window_days': WINDOW_DAYS,
        'start_date': start_date,
        'end_date': today,
    }
