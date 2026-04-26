from datetime import timedelta

import httpx
from django.core.management.base import BaseCommand
from django.utils import timezone

from races.models import Race


OPEN_METEO_URL = 'https://api.open-meteo.com/v1/forecast'
MAX_FORECAST_DAYS = 16  # Open-Meteo free tier limit


def _wind_direction_label(degrees):
    if degrees is None:
        return ''
    dirs = ['북', '북동', '동', '남동', '남', '남서', '서', '북서']
    idx = int((degrees + 22.5) // 45) % 8
    return dirs[idx]


def _format_wind(speed_kmh, direction_deg):
    if speed_kmh is None:
        return None
    label = _wind_direction_label(direction_deg)
    speed_ms = round(speed_kmh / 3.6, 1)
    if label:
        return f'{label}풍 {speed_ms} m/s'
    return f'{speed_ms} m/s'


class Command(BaseCommand):
    help = '임박한 대회의 날씨 예보를 Open-Meteo API에서 가져와 저장합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=MAX_FORECAST_DAYS,
            help=f'오늘부터 며칠 이내 대회를 대상으로 할지 (기본: {MAX_FORECAST_DAYS}, 최대: {MAX_FORECAST_DAYS})',
        )
        parser.add_argument(
            '--slug', type=str, default=None,
            help='특정 대회 slug 만 갱신 (디버깅용)',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='저장하지 않고 결과만 출력',
        )

    def handle(self, *args, **options):
        days = min(options['days'], MAX_FORECAST_DAYS)
        slug = options['slug']
        dry_run = options['dry_run']

        today = timezone.now().date()
        end_date = today + timedelta(days=days)

        qs = Race.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            race_date__gte=today,
            race_date__lte=end_date,
        )
        if slug:
            qs = qs.filter(slug=slug)

        total = qs.count()
        self.stdout.write(f'대상 대회: {total}개 (D-0 ~ D-{days})')
        if dry_run:
            self.stdout.write(self.style.WARNING('--dry-run 모드'))

        updated = 0
        failed = 0

        with httpx.Client(timeout=15.0) as client:
            for race in qs:
                try:
                    forecast = self._fetch(client, race)
                except Exception as exc:
                    failed += 1
                    self.stdout.write(self.style.ERROR(
                        f'  [실패] {race.slug}: {exc}'
                    ))
                    continue

                if not forecast:
                    self.stdout.write(f'  [스킵] {race.slug}: 예보 데이터 없음')
                    continue

                self.stdout.write(
                    f'  [OK] {race.slug}: '
                    f'{forecast["temp_low"]}~{forecast["temp_high"]}°C / '
                    f'비 {forecast["rain_prob"]}% / {forecast["wind"]}'
                )
                if not dry_run:
                    race.weather_forecast = forecast
                    race.save(update_fields=['weather_forecast', 'updated_at'])
                updated += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'완료: 갱신 {updated} / 실패 {failed} / 전체 {total}'
        ))

    def _fetch(self, client, race):
        race_date_str = race.race_date.isoformat()
        params = {
            'latitude': float(race.latitude),
            'longitude': float(race.longitude),
            'daily': ','.join([
                'temperature_2m_max',
                'temperature_2m_min',
                'precipitation_probability_max',
                'wind_speed_10m_max',
                'wind_direction_10m_dominant',
            ]),
            'timezone': 'Asia/Seoul',
            'start_date': race_date_str,
            'end_date': race_date_str,
        }
        resp = client.get(OPEN_METEO_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        daily = data.get('daily') or {}
        if not daily.get('time'):
            return None
        temp_high = (daily.get('temperature_2m_max') or [None])[0]
        temp_low = (daily.get('temperature_2m_min') or [None])[0]
        rain_prob = (daily.get('precipitation_probability_max') or [None])[0]
        wind_speed = (daily.get('wind_speed_10m_max') or [None])[0]
        wind_dir = (daily.get('wind_direction_10m_dominant') or [None])[0]
        return {
            'temp_high': round(temp_high, 1) if temp_high is not None else None,
            'temp_low': round(temp_low, 1) if temp_low is not None else None,
            'rain_prob': int(rain_prob) if rain_prob is not None else None,
            'wind': _format_wind(wind_speed, wind_dir),
            'fetched_at': timezone.now().isoformat(),
        }
