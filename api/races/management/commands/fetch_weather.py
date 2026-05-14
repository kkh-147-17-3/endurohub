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


# WMO Weather interpretation codes
# https://open-meteo.com/en/docs#weathervariables
_WEATHER_CODE_MAP = {
    0: ('맑음', '☀️'),
    1: ('대체로 맑음', '🌤️'),
    2: ('부분 흐림', '⛅'),
    3: ('흐림', '☁️'),
    45: ('안개', '🌫️'),
    48: ('짙은 안개', '🌫️'),
    51: ('약한 이슬비', '🌦️'),
    53: ('이슬비', '🌦️'),
    55: ('강한 이슬비', '🌦️'),
    56: ('어는 이슬비', '🌧️'),
    57: ('어는 이슬비', '🌧️'),
    61: ('약한 비', '🌧️'),
    63: ('비', '🌧️'),
    65: ('강한 비', '🌧️'),
    66: ('어는 비', '🌧️'),
    67: ('어는 비', '🌧️'),
    71: ('약한 눈', '🌨️'),
    73: ('눈', '🌨️'),
    75: ('많은 눈', '❄️'),
    77: ('싸락눈', '🌨️'),
    80: ('약한 소나기', '🌦️'),
    81: ('소나기', '🌦️'),
    82: ('강한 소나기', '⛈️'),
    85: ('약한 소낙눈', '🌨️'),
    86: ('소낙눈', '🌨️'),
    95: ('뇌우', '⛈️'),
    96: ('우박 동반 뇌우', '⛈️'),
    99: ('강한 우박 뇌우', '⛈️'),
}


def _interpret_weather_code(code):
    if code is None:
        return None, None
    label, icon = _WEATHER_CODE_MAP.get(int(code), (None, None))
    return label, icon


# 윈도우 내 대표 컨디션을 고를 때 사용하는 "심한 정도" 순위 (클수록 안 좋음)
_WEATHER_SEVERITY = {
    0: 0, 1: 1, 2: 2, 3: 3,
    45: 4, 48: 5,
    51: 6, 53: 7, 55: 8,
    61: 9, 80: 9,
    63: 10, 81: 10,
    65: 11, 82: 12,
    56: 13, 57: 14, 66: 15, 67: 16,
    71: 17, 73: 18, 75: 20, 77: 17,
    85: 18, 86: 19,
    95: 21, 96: 22, 99: 23,
}


def _format_wind(speed_kmh, direction_deg):
    if speed_kmh is None:
        return None
    label = _wind_direction_label(direction_deg)
    speed_ms = round(speed_kmh / 3.6, 1)
    if label:
        return f'{label}풍 {speed_ms} m/s'
    return f'{speed_ms} m/s'


def _hourly_sample(hourly, idx):
    def get(key):
        arr = hourly.get(key) or []
        return arr[idx] if idx < len(arr) else None
    code = get('weather_code')
    cond_label, cond_icon = _interpret_weather_code(code)
    temperature = get('temperature_2m')
    apparent = get('apparent_temperature')
    rain_prob = get('precipitation_probability')
    wind_speed = get('wind_speed_10m')
    wind_dir = get('wind_direction_10m')
    time = get('time')
    return {
        'time': time[-5:] if isinstance(time, str) and len(time) >= 5 else time,  # 'HH:MM'
        'temperature': round(temperature, 1) if temperature is not None else None,
        'apparent_temperature': round(apparent, 1) if apparent is not None else None,
        'rain_prob': int(rain_prob) if rain_prob is not None else None,
        'wind': _format_wind(wind_speed, wind_dir),
        'condition': cond_label,
        'condition_icon': cond_icon,
        'weather_code': int(code) if code is not None else None,
    }


def _summarize_window(samples):
    if not samples:
        return None
    temps = [s['temperature'] for s in samples if s['temperature'] is not None]
    feels = [s['apparent_temperature'] for s in samples if s['apparent_temperature'] is not None]
    rains = [s['rain_prob'] for s in samples if s['rain_prob'] is not None]
    coded = [s for s in samples if s['weather_code'] is not None]
    worst = max(
        coded,
        key=lambda s: _WEATHER_SEVERITY.get(s['weather_code'], 0),
        default=None,
    )
    windy = max(
        (s for s in samples if s.get('wind')),
        key=lambda s: float(s['wind'].split()[-2]) if s['wind'] and s['wind'].split()[-2].replace('.', '', 1).isdigit() else 0,
        default=None,
    )
    return {
        'start_time': samples[0]['time'],
        'end_time': samples[-1]['time'],
        'condition': worst['condition'] if worst else None,
        'condition_icon': worst['condition_icon'] if worst else None,
        'weather_code': worst['weather_code'] if worst else None,
        'temp_min': round(min(temps), 1) if temps else None,
        'temp_max': round(max(temps), 1) if temps else None,
        'apparent_temp_min': round(min(feels), 1) if feels else None,
        'apparent_temp_max': round(max(feels), 1) if feels else None,
        'rain_prob_max': max(rains) if rains else None,
        'wind': windy['wind'] if windy else None,
    }


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

                cond = forecast.get('condition') or '-'
                icon = forecast.get('condition_icon') or ''
                base_line = (
                    f'  [OK] {race.slug}: '
                    f'{icon} {cond} / '
                    f'{forecast["temp_low"]}~{forecast["temp_high"]}°C / '
                    f'비 {forecast["rain_prob"]}% / {forecast["wind"]}'
                )
                rw = forecast.get('race_window')
                if rw:
                    base_line += (
                        f"  ⏱ {rw['start_time']}~{rw['end_time']} "
                        f"{rw.get('condition_icon') or ''} {rw.get('condition') or '-'} "
                        f"{rw['temp_min']}~{rw['temp_max']}°C "
                        f"(체감 {rw['apparent_temp_min']}~{rw['apparent_temp_max']}°C) "
                        f"비 {rw['rain_prob_max']}%"
                    )
                self.stdout.write(base_line)
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
                'weather_code',
                'temperature_2m_max',
                'temperature_2m_min',
                'precipitation_probability_max',
                'wind_speed_10m_max',
                'wind_direction_10m_dominant',
            ]),
            'hourly': ','.join([
                'weather_code',
                'temperature_2m',
                'apparent_temperature',
                'precipitation_probability',
                'wind_speed_10m',
                'wind_direction_10m',
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
        weather_code = (daily.get('weather_code') or [None])[0]
        condition_label, condition_icon = _interpret_weather_code(weather_code)

        forecast = {
            'temp_high': round(temp_high, 1) if temp_high is not None else None,
            'temp_low': round(temp_low, 1) if temp_low is not None else None,
            'rain_prob': int(rain_prob) if rain_prob is not None else None,
            'wind': _format_wind(wind_speed, wind_dir),
            'condition': condition_label,
            'condition_icon': condition_icon,
            'weather_code': int(weather_code) if weather_code is not None else None,
            'fetched_at': timezone.now().isoformat(),
        }

        # 출발시각이 있으면 해당 시각 ~ +3시간 윈도우의 시간별 예보를 추출
        hourly = data.get('hourly') or {}
        if race.start_time and hourly.get('time'):
            window = self._extract_race_window(hourly, race)
            if window:
                forecast['race_hours'] = window
                forecast['race_window'] = _summarize_window(window)
        return forecast

    def _extract_race_window(self, hourly, race):
        # API 응답은 'YYYY-MM-DDTHH:MM' 문자열 (Asia/Seoul). 출발시간 정각으로 내려서 매칭.
        start_hour = race.start_time.hour
        target_prefix = f'{race.race_date.isoformat()}T{start_hour:02d}:00'
        times = hourly.get('time') or []
        try:
            start_idx = times.index(target_prefix)
        except ValueError:
            return None
        # 출발 ~ 출발+3h (총 4 시점)
        samples = []
        for offset in range(4):
            idx = start_idx + offset
            if idx >= len(times):
                break
            samples.append(_hourly_sample(hourly, idx))
        return samples
