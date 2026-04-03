import logging

from celery import shared_task

from races.emails import send_crawl_report_email
from races.services import MarathonCrawlerService

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def crawl_marathon_task(year=None, month=None, with_details=True):
    service = MarathonCrawlerService()
    crawl_func = service.crawl_with_details if with_details else service.crawl
    result = crawl_func(year=year, month=month, dry_run=False)
    email_sent = send_crawl_report_email(
        result,
        crawl_type='detailed' if with_details else 'basic',
    )
    logger.info(
        'Crawl marathon task completed',
        extra={
            'year': year,
            'month': month,
            'with_details': with_details,
            'created_count': result.get('created', 0),
            'updated_count': result.get('updated', 0),
            'skipped_count': result.get('skipped', 0),
            'email_sent': email_sent,
        },
    )
