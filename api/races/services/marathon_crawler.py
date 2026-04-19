import json
import logging
import re
import time
from datetime import date, datetime, time as dt_time, timedelta
from decimal import Decimal

import httpx
from django.utils import timezone

from races.models import Race, RacePendingChange

logger = logging.getLogger(__name__)


class MarathonCrawlerService:
    SOURCE_URL = 'http://www.roadrun.co.kr/schedule/list.php'
    DETAIL_URL = 'http://www.roadrun.co.kr/schedule/view.php?no='
    CRITICAL_FIELDS = [
        'race_date',
        'race_end_date',
        'location',
        'registration_start',
        'registration_end',
    ]

    def __init__(self):
        self.region_map = {
            '서울': '서울',
            '경기': '경기',
            '인천': '인천',
            '강원': '강원',
            '충북': '충북',
            '충남': '충남',
            '대전': '대전',
            '세종': '세종',
            '전북': '전북',
            '전남': '전남',
            '광주': '광주',
            '대구': '대구',
            '경북': '경북',
            '경남': '경남',
            '부산': '부산',
            '울산': '울산',
            '제주': '제주',
        }
        self.extra_patterns = {
            '청주': '충북',
            '천안': '충남',
            '전주': '전북',
            '목포': '전남',
            '여수': '전남',
            '순천': '전남',
            '포항': '경북',
            '구미': '경북',
            '경주': '경북',
            '창원': '경남',
            '김해': '경남',
            '거제': '경남',
            '통영': '경남',
            '속초': '강원',
            '춘천': '강원',
            '원주': '강원',
            '강릉': '강원',
            '수원': '경기',
            '용인': '경기',
            '성남': '경기',
            '고양': '경기',
            '부천': '경기',
            '안산': '경기',
            '안양': '경기',
            '평택': '경기',
            '파주': '경기',
            '김포': '경기',
            '광명': '경기',
            '하남': '경기',
        }

    def crawl(self, year=None, month=None, dry_run=False):
        year = year or timezone.now().year
        html = self._fetch_list_html(year, month)
        races = self.parse_html(html, year)

        if dry_run:
            return {
                'success': True,
                'total': len(races),
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'races': races,
            }

        return self._persist_races(races, self.save_race, 'Marathon crawl completed')

    def crawl_with_details(self, year=None, month=None, dry_run=False):
        year = year or timezone.now().year
        html = self._fetch_list_html(year, month)
        races = self.parse_html(html, year)

        detailed_races = []
        for race in races:
            race_no = int(race['race_no'])
            detail = self.crawl_detail(race_no)
            if detail:
                detailed_races.append({**race, **detail})
            else:
                race['_detail_failed'] = True
                detailed_races.append(race)
            time.sleep(0.2)

        if dry_run:
            return {
                'success': True,
                'total': len(detailed_races),
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'races': detailed_races,
            }

        return self._persist_races(
            detailed_races,
            self.save_detailed_race,
            'Marathon detailed crawl completed',
        )

    def crawl_detail(self, race_no):
        response = httpx.get(
            f'{self.DETAIL_URL}{race_no}',
            timeout=30,
            verify=False,
        )
        if response.status_code != 200:
            logger.warning('Race detail crawl failed', extra={'race_no': race_no, 'status': response.status_code})
            return None
        html = self._decode_body(response.content)
        return self.parse_detail_html(html, race_no)

    def parse_html(self, html, year):
        races = []
        pattern = re.compile(
            r'<tr>\s*<td[^>]*>\s*<div[^>]*><b><font[^>]*>(\d{1,2})\/(\d{1,2})<\/font><\/b>'
            r'<br><font[^>]*>\(([일월화수목금토])\)<\/font>.*?<\/div>\s*<\/td>\s*'
            r'<td[^>]*><b><font[^>]*><a[^>]*view\.php\?no=(\d+)[^>]*>'
            r'((?:[^<]+|<br\s*\/?>)*)<\/a>(?:<img[^>]*>)?<br><font[^>]*>([^<]*)<\/font>'
            r'<\/font><\/b><\/td>\s*<td[^>]*>\s*<div[^>]*>((?:[^<]+|<br\s*\/?>)*)'
            r'<\/div>\s*<\/td>\s*<td[^>]*>\s*<div[^>]*>([^<]*)<br>\s*☎([^<]*)<br>(.*?)'
            r'<\/div>\s*<\/td>\s*<\/tr>',
            re.IGNORECASE | re.DOTALL,
        )

        for match in pattern.finditer(html):
            month = int(match.group(1))
            day = int(match.group(2))
            race_no = match.group(4)
            title = self._clean_html_text(match.group(5))
            distances = self.parse_distances(match.group(6))
            location = self._clean_html_text(match.group(7))
            organizer = self._clean_html_text(match.group(8))
            phone = match.group(9).strip()
            extra_html = match.group(10) or ''

            official_url = None
            url_match = re.search(r'href="(https?:\/\/[^"]+)"[^>]*target="_new"', extra_html, re.IGNORECASE)
            if url_match:
                official_url = url_match.group(1)

            races.append({
                'race_no': race_no,
                'title': title,
                'race_date': self.normalize_date(year, month, day),
                'day_of_week': match.group(3),
                'distances': distances,
                'location': location,
                'region': self.detect_region(location),
                'organizer': organizer,
                'phone': phone,
                'official_url': official_url,
                'source_url': f'{self.DETAIL_URL}{race_no}',
            })

        return races

    def parse_detail_html(self, html, race_no):
        data = {
            'external_id': str(race_no),
            'source_url': f'{self.DETAIL_URL}{race_no}',
        }

        title = re.search(r'<td[^>]*>.*?대회명.*?<\/td>\s*<td[^>]*>.*?<B>([^<]+)<\/B>', html, re.IGNORECASE | re.DOTALL)
        if title:
            data['title'] = self._clean_html_text(title.group(1))

        representative = re.search(
            r'<td[^>]*>.*?대표자명.*?<\/td>\s*<td[^>]*>.*?<p>([^<]+)<\/p>',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if representative:
            data['representative'] = representative.group(1).strip()

        email = re.search(r'mail_url=([^\'"&]+)', html, re.IGNORECASE)
        if email:
            data['organizer_email'] = email.group(1).strip()

        date_time_match = re.search(
            r'<td[^>]*>.*?대회일시.*?<\/td>\s*<td[^>]*>.*?<p>([^<]+)<\/p>',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if date_time_match:
            date_time_text = date_time_match.group(1).strip()
            date_match = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', date_time_text)
            if date_match:
                data['race_date'] = self.normalize_date(
                    int(date_match.group(1)),
                    int(date_match.group(2)),
                    int(date_match.group(3)),
                )
            time_match = re.search(r'출발시간\s*:\s*(\d{1,2}):(\d{2})', date_time_text)
            if time_match:
                data['start_time'] = dt_time(hour=int(time_match.group(1)), minute=int(time_match.group(2)))

        organizer_contact = re.search(
            r'<td[^>]*>.*?전화번호.*?<\/td>\s*<td[^>]*>([^<]+)',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if organizer_contact:
            data['organizer_contact'] = self._clean_html_text(organizer_contact.group(1))

        distances = re.search(
            r'<td[^>]*>.*?대회종목.*?<\/td>\s*<td[^>]*>([^<]+)',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if distances:
            data['distances'] = self.parse_distances(distances.group(1))

        region = re.search(
            r'<td[^>]*>.*?대회지역.*?<\/td>\s*<td[^>]*>([^<]+)',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if region:
            value = region.group(1).strip()
            data['region'] = self.region_map.get(value, value or '기타')

        location = re.search(
            r'<td[^>]*>.*?대회장소.*?<\/td>\s*<td[^>]*>.*?<p>([^<]+)<\/p>',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if location:
            data['location'] = self._clean_html_text(location.group(1))

        organizer = re.search(
            r'<td[^>]*>.*?주최단체.*?<\/td>\s*<td[^>]*>.*?<p>([^<]+)<\/p>',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if organizer:
            data['organizer'] = self._clean_html_text(organizer.group(1))

        period = re.search(
            r'<td[^>]*>.*?접수기간.*?<\/td>\s*<td[^>]*>([^<]+)',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if period:
            period_text = period.group(1).strip()
            start_match = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', period_text)
            if start_match:
                data['registration_start'] = self.normalize_date(
                    int(start_match.group(1)),
                    int(start_match.group(2)),
                    int(start_match.group(3)),
                )
            end_match = re.search(r'~\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', period_text)
            if end_match:
                data['registration_end'] = self.normalize_date(
                    int(end_match.group(1)),
                    int(end_match.group(2)),
                    int(end_match.group(3)),
                )

        homepage = re.search(
            r'<td[^>]*>.*?홈페이지.*?<\/td>\s*<td[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*target="_new"',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if homepage:
            data['official_url'] = homepage.group(1).strip()

        description = re.search(
            r'<td[^>]*>.*?기타소개.*?<\/td>\s*<td[^>]*>.*?<p>(.*?)<\/p>',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if description:
            raw = self._clean_html_text(description.group(1))
            data['description'] = re.sub(r'\s+', ' ', raw).strip()

        lat_lng = re.search(
            r'center:\s*new\s+naver\.maps\.LatLng\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)',
            html,
            re.IGNORECASE,
        )
        if lat_lng:
            data['latitude'] = Decimal(lat_lng.group(1))
            data['longitude'] = Decimal(lat_lng.group(2))

        address = re.search(r"iw_inner[^']*',\s*'([^']+)',", html, re.IGNORECASE)
        if address:
            cleaned = re.sub(r'[\r\n\t]+', ' ', address.group(1))
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            if cleaned and len(cleaned) > 3:
                data['address'] = cleaned

        return data

    def parse_distances(self, distance_string):
        distance_string = self._clean_html_text(distance_string)
        if not distance_string:
            return []

        distances = []
        seen_names = set()
        for part in re.split(r'[,\s]+', distance_string):
            part = part.strip()
            if not part:
                continue
            normalized = part
            if '풀' in part:
                normalized = '42.195km'
            elif '하프' in part:
                normalized = '21.0975km'
            elif '100km' in part:
                normalized = '100km'
            elif '울트라' in part:
                normalized = 'Ultra'
            else:
                km_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|KM)', part)
                if km_match:
                    normalized = f'{km_match.group(1)}km'
                else:
                    short_k_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:k|K)$', part)
                    if short_k_match:
                        normalized = f'{short_k_match.group(1)}km'
            if normalized not in seen_names:
                seen_names.add(normalized)
                km = Race.parse_distance_km(normalized)
                item = {'name': normalized}
                if km is not None:
                    item['distance_meter'] = round(km * 1000)
                distances.append(item)
        return distances

    def detect_region(self, location):
        for keyword, region in self.region_map.items():
            if keyword in location:
                return region
        for keyword, region in self.extra_patterns.items():
            if keyword in location:
                return region
        return '기타'

    def normalize_date(self, year, month, day):
        last_day = (date(year + (month // 12), (month % 12) + 1, 1) - timedelta(days=1)).day if month != 12 else 31
        day = min(day, last_day)
        return date(year, month, day)

    def build_description(self, data):
        parts = []
        if data.get('organizer'):
            parts.append(f"주최: {data['organizer']}")
        if data.get('phone'):
            parts.append(f"연락처: {data['phone']}")
        return '\n'.join(parts)

    def save_race(self, data):
        existing = Race.objects.filter(source_url=data['source_url']).first()
        race_data = {
            'title': data['title'],
            'sport': 'running',
            'race_date': data['race_date'],
            'location': data['location'],
            'region': data['region'],
            'distances': data['distances'],
            'official_url': data['official_url'],
            'source': 'crawl',
            'source_url': data['source_url'],
            'description': self.build_description(data),
        }
        return self._save_race_record(existing, race_data, detailed=False)

    def save_detailed_race(self, data):
        external_id = data.get('external_id') or data.get('race_no')
        existing = None
        if external_id:
            existing = Race.objects.filter(external_id=str(external_id)).first()
        if not existing and data.get('source_url'):
            existing = Race.objects.filter(source_url=data['source_url']).first()

        if data.get('_detail_failed') and existing:
            return {'status': 'skipped', 'race': existing, 'reason': 'detail_crawl_failed'}

        race_data = {
            'title': data.get('title', ''),
            'sport': 'running',
            'race_date': data.get('race_date'),
            'start_time': data.get('start_time'),
            'location': data.get('location', ''),
            'address': data.get('address'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'region': data.get('region', '기타'),
            'distances': data.get('distances', []),
            'registration_start': data.get('registration_start'),
            'registration_end': data.get('registration_end'),
            'official_url': data.get('official_url'),
            'source': 'crawl',
            'source_url': data.get('source_url'),
            'external_id': str(external_id) if external_id else None,
            'description': data.get('description'),
            'organizer': data.get('organizer'),
            'organizer_contact': data.get('organizer_contact'),
            'organizer_email': data.get('organizer_email'),
        }
        return self._save_race_record(existing, race_data, detailed=True)

    def _save_race_record(self, existing, race_data, detailed):
        if existing:
            if not existing.auto_update_enabled:
                return {'status': 'skipped', 'race': existing, 'reason': 'auto_update_disabled'}

            changes = self._get_changes(existing, race_data, detailed=detailed)
            if not changes:
                return {'status': 'skipped', 'race': existing}

            locked_fields = existing.locked_fields or []
            auto_apply_fields = {'description'}
            allowed_changes = {}
            pending_changes = {}

            for field, change in changes.items():
                if field in locked_fields:
                    pending_changes[field] = change
                    continue
                if existing.verified_at and field not in auto_apply_fields:
                    pending_changes[field] = change
                    continue
                if not existing.verified_at and field in self.CRITICAL_FIELDS:
                    pending_changes[field] = change
                    continue
                allowed_changes[field] = change

            for field, change in pending_changes.items():
                self._upsert_pending_change(existing, field, change['old'], change['new'])

            if allowed_changes:
                update_fields = []
                for field in allowed_changes:
                    setattr(existing, field, race_data.get(field))
                    update_fields.append(field)
                existing.save(update_fields=update_fields + ['updated_at'])

            return {
                'status': 'updated' if allowed_changes else 'pending',
                'race': existing,
                'applied_changes': allowed_changes,
                'pending_changes': pending_changes,
            }

        create_data = {
            **race_data,
            'slug': Race.generate_unique_slug(race_data['title']),
        }
        race = Race.objects.create(**create_data)
        return {'status': 'created', 'race': race}

    def _get_changes(self, existing, new_data, detailed=False):
        changes = {}
        compare_fields = [
            'title',
            'race_date',
            'location',
            'region',
            'official_url',
            'description',
        ]
        if detailed:
            compare_fields = [
                'title',
                'race_date',
                'start_time',
                'location',
                'address',
                'latitude',
                'longitude',
                'region',
                'registration_start',
                'registration_end',
                'official_url',
                'description',
                'organizer',
                'organizer_contact',
                'organizer_email',
            ]

        for field in compare_fields:
            old_value = self._normalize_for_compare(getattr(existing, field))
            new_value = self._normalize_for_compare(new_data.get(field))
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}

        old_names = sorted(Race.distance_names(existing.distances or []))
        new_names = sorted(Race.distance_names(new_data.get('distances') or []))
        if old_names != new_names:
            changes['distances'] = {'old': existing.distances, 'new': new_data.get('distances')}

        return changes

    def _upsert_pending_change(self, race, field_name, old_value, new_value):
        new_value_text = self._serialize_pending_value(new_value)
        existing_pending = RacePendingChange.objects.filter(
            race_id=race.id,
            field_name=field_name,
            status='pending',
        ).first()
        if existing_pending:
            existing_pending.new_value = new_value_text
            existing_pending.save(update_fields=['new_value', 'updated_at'])
            return

        recently_reviewed = RacePendingChange.objects.filter(
            race_id=race.id,
            field_name=field_name,
            status__in=['approved', 'rejected'],
            reviewed_at__gte=timezone.now() - timedelta(days=30),
            new_value=new_value_text,
        ).exists()
        if recently_reviewed:
            return

        RacePendingChange.objects.create(
            race_id=race.id,
            field_name=field_name,
            old_value=self._serialize_pending_value(old_value),
            new_value=new_value_text,
            source='crawler',
        )

    def _persist_races(self, races, save_func, log_message):
        created = 0
        updated = 0
        skipped = 0
        created_races = []
        updated_races = []

        for race_data in races:
            result = save_func(race_data)
            if result['status'] == 'created':
                created += 1
                created_races.append(result['race'])
            elif result['status'] == 'updated':
                updated += 1
                updated_races.append(result)
            else:
                skipped += 1

        logger.info(
            log_message,
            extra={'total': len(races), 'created_count': created, 'updated_count': updated, 'skipped_count': skipped},
        )
        return {
            'success': True,
            'total': len(races),
            'created': created,
            'updated': updated,
            'skipped': skipped,
            'createdRaces': created_races,
            'updatedRaces': updated_races,
        }

    def _fetch_list_html(self, year, month):
        response = httpx.post(
            self.SOURCE_URL,
            data={
                'syear_key': year,
                'smonth_key': month or '',
                'course1_key': '',
                'syoil_key': '',
                'take_key': '',
                'area_key': '',
                'search_f': '',
                'search_k': '',
            },
            timeout=30,
            verify=False,
        )
        if response.status_code >= 400:
            logger.error('Marathon crawl failed', extra={'status': response.status_code})
            raise RuntimeError('HTTP request failed')
        return self._decode_body(response.content)

    def _decode_body(self, content):
        return content.decode('cp949', errors='replace')

    def _clean_html_text(self, value):
        text = re.sub(r'<br\s*/?>', ' ', value, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ')
        return re.sub(r'\s+', ' ', text).strip()

    def _normalize_for_compare(self, value):
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, dt_time):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value.normalize())
        return value

    def _serialize_pending_value(self, value):
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, dt_time):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        return value
