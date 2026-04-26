import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from races.constants import SPORT_CODES
from races.models import RacePendingChange

logger = logging.getLogger(__name__)


def _inject_sport_code(races):
    for race in races:
        sport = getattr(race, 'sport', None)
        race.sport_code = SPORT_CODES.get(sport, sport[:3].upper() if sport else '')
    return races


def send_crawl_report_email(result, crawl_type='detailed'):
    created = result.get('created', 0)
    updated = result.get('updated', 0)
    has_changes = created > 0 or updated > 0
    if not has_changes and not settings.CRAWL_SEND_EMPTY_REPORT:
        return False

    if not getattr(settings, 'EMAIL_HOST_USER', ''):
        logger.warning('EMAIL_HOST_USER not configured, skipping crawl report email')
        return False

    updated_items = _build_updated_items(result.get('updatedRaces', []))
    _inject_sport_code(result.get('createdRaces', []))
    _inject_sport_code(item['race'] for item in updated_items)

    context = {
        'result': result,
        'crawl_type': crawl_type,
        'updated_items': updated_items,
    }
    subject = f'[크롤링 리포트] 신규 {created}건, 업데이트 {updated}건'
    html_body = render_to_string('emails/crawl_report.html', context)
    text_body = _build_text_body(result)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CRAWL_REPORT_EMAIL],
    )
    message.attach_alternative(html_body, 'text/html')
    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception('Failed to send crawl report email')
        return False
    return True


def _build_updated_items(updated_races):
    items = []
    for item in updated_races:
        items.append({
            'race': item['race'],
            'applied_changes': _build_change_list(item.get('applied_changes', {})),
            'pending_changes': _build_change_list(item.get('pending_changes', {})),
        })
    return items


def _build_change_list(changes):
    field_labels = RacePendingChange.FIELD_LABELS
    rows = []
    for field_name, change in changes.items():
        rows.append({
            'field_name': field_name,
            'field_label': field_labels.get(field_name, field_name),
            'old_value': _format_display_value(change.get('old')),
            'new_value': _format_display_value(change.get('new')),
        })
    return rows


def _format_display_value(value):
    if value is None or value == '':
        return '-'
    if isinstance(value, list):
        return ', '.join(str(v) for v in value) or '-'
    if isinstance(value, dict):
        return ', '.join(f'{k}: {v}' for k, v in value.items()) or '-'
    return str(value)


def _build_text_body(result):
    lines = [
        '마라톤 대회 크롤링 리포트',
        '',
        f"전체: {result.get('total', 0)}",
        f"신규: {result.get('created', 0)}",
        f"업데이트: {result.get('updated', 0)}",
        f"스킵: {result.get('skipped', 0)}",
    ]
    created_races = result.get('createdRaces', [])
    if created_races:
        lines.extend(['', '신규 등록된 대회'])
        lines.extend(f'- {race.title}' for race in created_races)
    return '\n'.join(lines)
