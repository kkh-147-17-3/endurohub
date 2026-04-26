import re
from datetime import date

from django.conf import settings
from django.db import models
from django.utils import timezone

from .constants import (
    DISTANCE_CATEGORIES,
    SPORT_LABELS,
    STATUS_LABELS,
    TRAIL_RUNNING_KEYWORDS,
)
from .image_utils import get_thumb_path, get_webp_path


class RaceQuerySet(models.QuerySet):

    def upcoming(self):
        today = timezone.now().date()
        return self.filter(race_date__gte=today).order_by('race_date')

    def closing_soon(self, days=7):
        today = timezone.now().date()
        end_date = today + timezone.timedelta(days=days)
        return self.exclude(
            status='registration_closed'
        ).extra(
            where=["COALESCE(race_end_date, race_date) >= %s"],
            params=[today],
        ).filter(
            registration_end__gte=today,
            registration_end__lte=end_date,
        ).order_by('registration_end')

    def by_month_range(self, month_from=None, month_to=None):
        from datetime import datetime
        qs = self
        if month_from:
            start = datetime.strptime(month_from, '%Y-%m').date().replace(day=1)
            qs = qs.filter(race_date__gte=start)
        if month_to:
            dt = datetime.strptime(month_to, '%Y-%m').date()
            import calendar
            last_day = calendar.monthrange(dt.year, dt.month)[1]
            end = dt.replace(day=last_day)
            qs = qs.filter(race_date__lte=end)
        return qs.order_by('race_date')

    def by_sport(self, sport):
        if isinstance(sport, (list, tuple)):
            return self.filter(sport__in=sport)
        return self.filter(sport=sport)

    def by_region(self, region):
        if isinstance(region, (list, tuple)):
            return self.filter(region__in=region)
        return self.filter(region=region)

    def by_status(self, statuses):
        from django.db.models import Q
        if isinstance(statuses, str):
            statuses = [statuses]
        today = timezone.now().date()
        q = Q()
        for s in statuses:
            # Manual status override
            status_q = Q(status=s)
            # Auto-calculated based on dates (when status is NULL)
            auto_q = Q(status__isnull=True) | Q(status='')
            if s == 'finished':
                auto_q &= (
                    Q(race_end_date__lt=today, race_end_date__isnull=False) |
                    Q(race_end_date__isnull=True, race_date__lt=today)
                )
            elif s == 'registration_open':
                auto_q &= Q(
                    registration_start__isnull=False,
                    registration_end__isnull=False,
                    registration_start__lte=today,
                    registration_end__gte=today,
                )
                # Also ensure race hasn't finished
                auto_q &= (
                    Q(race_end_date__gte=today) |
                    Q(race_end_date__isnull=True, race_date__gte=today)
                )
            elif s == 'registration_closed':
                auto_q &= Q(
                    registration_end__isnull=False,
                    registration_end__lt=today,
                )
                auto_q &= (
                    Q(race_end_date__gte=today) |
                    Q(race_end_date__isnull=True, race_date__gte=today)
                )
            elif s == 'upcoming':
                auto_q &= (
                    Q(race_end_date__gte=today) |
                    Q(race_end_date__isnull=True, race_date__gte=today)
                )
                auto_q &= (
                    Q(registration_end__isnull=True) |
                    Q(registration_end__gte=today)
                )
                auto_q &= (
                    Q(registration_start__isnull=True) |
                    Q(registration_end__isnull=True) |
                    Q(registration_start__gt=today)
                )
            q |= (status_q | auto_q)
        return self.filter(q)

    def by_name(self, name):
        return self.filter(title__icontains=name)

    def by_distance_category(self, sport, categories):
        """Filter by distance category using Python-based matching.

        Uses Race.parse_distance_km to handle distance strings like '42.195km', '1,800m'.
        Works with both json and jsonb column types.
        """
        if isinstance(categories, str):
            categories = [categories]
        sport_categories = DISTANCE_CATEGORIES.get(sport, [])
        if not sport_categories or not categories:
            return self

        cats = []
        for cat_value in categories:
            cat = next((c for c in sport_categories if c['value'] == cat_value), None)
            if cat:
                cats.append(cat)
        if not cats:
            return self

        # Fetch candidates with distances and filter in Python
        candidates = self.filter(distances__isnull=False)
        matching_ids = []
        for race in candidates.only('id', 'distances'):
            dists = race.distances
            if not isinstance(dists, list) or not dists:
                continue
            names = Race.distance_names(dists)
            for cat in cats:
                cat_type = cat['type']
                if cat_type == 'range':
                    for name in names:
                        km = Race.parse_distance_km(name)
                        if km is not None and cat['min'] <= km <= cat['max']:
                            matching_ids.append(race.id)
                            break
                    else:
                        continue
                    break
                elif cat_type == 'range_m':
                    for name in names:
                        km = Race.parse_distance_km(name)
                        if km is not None:
                            m = km * 1000.0
                            if cat['min'] <= m <= cat['max']:
                                matching_ids.append(race.id)
                                break
                    else:
                        continue
                    break
                elif cat_type == 'keyword':
                    keyword = cat['keyword'].lower()
                    for name in names:
                        if keyword in name.lower():
                            matching_ids.append(race.id)
                            break
                    else:
                        continue
                    break
                elif cat_type == 'non_numeric':
                    for name in names:
                        if name.strip() and not re.match(r'^[\d]', name.strip()):
                            matching_ids.append(race.id)
                            break
                    else:
                        continue
                    break

        return self.filter(pk__in=matching_ids)

    def registration_open(self):
        from django.db.models import Q
        today = timezone.now().date()
        return self.filter(
            Q(status='registration_open') |
            Q(
                Q(status__isnull=True) | Q(status=''),
                registration_start__isnull=False,
                registration_end__isnull=False,
                registration_start__lte=today,
                registration_end__gte=today,
            ) & (
                Q(race_end_date__gte=today) |
                Q(race_end_date__isnull=True, race_date__gte=today)
            )
        )


class Race(models.Model):
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=255, unique=True)
    sport = models.CharField(max_length=20)
    edition = models.CharField(max_length=50, null=True, blank=True)
    race_date = models.DateField()
    race_end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=100)
    address = models.CharField(max_length=200, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    region = models.CharField(max_length=50)
    distances = models.JSONField(null=True, blank=True)
    registration_start = models.DateField(null=True, blank=True)
    registration_end = models.DateField(null=True, blank=True)
    registration_phases = models.JSONField(null=True, blank=True)
    official_url = models.CharField(max_length=500, null=True, blank=True)
    recap_url = models.CharField(max_length=500, null=True, blank=True)
    ai_summary = models.TextField(null=True, blank=True)
    source = models.CharField(max_length=20, default='manual')
    source_url = models.CharField(max_length=500, null=True, blank=True)
    external_id = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=30, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    organizer = models.CharField(max_length=100, null=True, blank=True)
    organizer_contact = models.CharField(max_length=100, null=True, blank=True)
    organizer_email = models.CharField(max_length=100, null=True, blank=True)
    image_url = models.CharField(max_length=500, null=True, blank=True)
    image_path = models.CharField(max_length=500, null=True, blank=True)
    giveaways = models.JSONField(null=True, blank=True)
    course_images = models.JSONField(null=True, blank=True)
    giveaway_images = models.JSONField(null=True, blank=True)
    course_image_uploads = models.JSONField(null=True, blank=True)
    giveaway_image_uploads = models.JSONField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    weather_forecast = models.JSONField(null=True, blank=True)
    course_surface = models.CharField(max_length=100, null=True, blank=True)
    course_difficulty = models.CharField(max_length=100, null=True, blank=True)
    aid_stations = models.CharField(max_length=100, null=True, blank=True)
    timing_method = models.CharField(max_length=100, null=True, blank=True)
    parking = models.CharField(max_length=100, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.CharField(max_length=255, null=True, blank=True)
    locked_fields = models.JSONField(null=True, blank=True)
    auto_update_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RaceQuerySet.as_manager()

    class Meta:
        db_table = 'races'
        ordering = ['race_date']

    def save(self, **kwargs):
        if self.sport == 'running' and self._title_matches_trail_running():
            self.sport = 'trail_running'
        self._fill_distance_meters()
        super().save(**kwargs)

    def _fill_distance_meters(self):
        """Auto-calculate distance_meter from name when not set."""
        if not self.distances or not isinstance(self.distances, list):
            return
        for d in self.distances:
            if isinstance(d, dict) and 'name' in d and not d.get('distance_meter'):
                km = Race.parse_distance_km(d['name'])
                if km is not None:
                    d['distance_meter'] = round(km * 1000)

    def _title_matches_trail_running(self):
        title_lower = self.title.lower()
        return any(kw.lower() in title_lower for kw in TRAIL_RUNNING_KEYWORDS)

    def __str__(self):
        return self.title

    @property
    def computed_status(self):
        """Return status from DB if set, otherwise calculate from dates."""
        if self.status:
            return self.status
        today = timezone.now().date()
        end_date = self.race_end_date or self.race_date
        if end_date and end_date < today:
            return 'finished'
        if self.registration_start and self.registration_end:
            if self.registration_start <= today <= self.registration_end:
                return 'registration_open'
        if self.registration_end and self.registration_end < today:
            return 'registration_closed'
        return 'upcoming'

    @property
    def sport_label(self):
        return SPORT_LABELS.get(self.sport, self.sport)

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.computed_status, self.computed_status)

    @property
    def image_src(self):
        if self.image_url:
            return self.image_url
        if self.image_path:
            webp = get_webp_path(self.image_path)
            return f'{settings.STORAGE_URL}{webp}'
        return None

    @property
    def image_src_thumb(self):
        if self.image_url:
            return self.image_url
        if self.image_path:
            thumb = get_thumb_path(self.image_path)
            if thumb:
                return f'{settings.STORAGE_URL}{thumb}'
            return self.image_src
        return None

    @property
    def course_image_srcs(self):
        images = []
        if self.course_images:
            images.extend(self._resolve_image_urls(self.course_images))
        if self.course_image_uploads:
            images.extend(
                f'{settings.STORAGE_URL}{get_webp_path(p)}' for p in self.course_image_uploads
            )
        return images

    @property
    def giveaway_image_srcs(self):
        images = []
        if self.giveaway_images:
            images.extend(self._resolve_image_urls(self.giveaway_images))
        if self.giveaway_image_uploads:
            images.extend(
                f'{settings.STORAGE_URL}{get_webp_path(p)}' for p in self.giveaway_image_uploads
            )
        return images

    @property
    def days_until_race(self):
        if not self.race_date:
            return 0
        return (self.race_date - timezone.now().date()).days

    @property
    def days_until_registration_end(self):
        if not self.registration_end:
            return None
        return (self.registration_end - timezone.now().date()).days

    @property
    def is_registration_open(self):
        return self.computed_status == 'registration_open'

    @property
    def is_verified(self):
        return self.verified_at is not None

    @property
    def url(self):
        return f'/races/{self.slug}'

    def _resolve_image_urls(self, paths):
        resolved = []
        for path in paths:
            if isinstance(path, str):
                if path.startswith(('http://', 'https://')):
                    resolved.append(path)
                else:
                    resolved.append(f'{settings.STORAGE_URL}{path}')
        return resolved

    def is_field_locked(self, field):
        return field in (self.locked_fields or [])

    @staticmethod
    def parse_distance_km(distance_string):
        """Extract km value from distance strings like '42.195km', '10km', '1,800m'."""
        if not distance_string or not isinstance(distance_string, str):
            return None
        s = distance_string.strip()
        # Try km pattern first: e.g. "42.195km", "10km", "10.5"
        km_match = re.search(r'([\d,]+\.?\d*)\s*(?:km|K)', s, re.IGNORECASE)
        if km_match:
            try:
                return float(km_match.group(1).replace(',', ''))
            except (ValueError, TypeError):
                return None
        # Try meters pattern: e.g. "1,800m", "800m"
        m_match = re.search(r'([\d,]+\.?\d*)\s*m\b', s, re.IGNORECASE)
        if m_match:
            try:
                return float(m_match.group(1).replace(',', '')) / 1000.0
            except (ValueError, TypeError):
                return None
        # Try bare number (assume km)
        bare_match = re.match(r'^([\d,]+\.?\d*)$', s)
        if bare_match:
            try:
                return float(bare_match.group(1).replace(',', ''))
            except (ValueError, TypeError):
                return None
        return None

    @staticmethod
    def distance_names(distances):
        """Extract name strings from distances (supports both old and new format).

        Old format: ["50km", "30km"]
        New format: [{"name": "50km", "distance_km": 50, ...}, ...]
        Returns: ["50km", "30km"]
        """
        if not distances or not isinstance(distances, list):
            return []
        names = []
        for d in distances:
            if isinstance(d, str):
                names.append(d)
            elif isinstance(d, dict) and 'name' in d:
                names.append(d['name'])
        return names

    @staticmethod
    def detect_distance_category(distances, sport):
        """Find matching distance category for given distances and sport.

        Finds max km from distances array, then matches against DISTANCE_CATEGORIES rules.
        Falls back to keyword matching if numeric match fails.
        """
        if not distances or not sport:
            return None
        sport_categories = DISTANCE_CATEGORIES.get(sport, [])
        if not sport_categories:
            return None

        names = Race.distance_names(distances)

        # Parse all distances to find max km
        km_values = []
        for name in names:
            km = Race.parse_distance_km(name)
            if km is not None:
                km_values.append(km)
        max_km = max(km_values) if km_values else None

        # Try numeric range matching first
        if max_km is not None:
            for cat in sport_categories:
                cat_type = cat.get('type')
                if cat_type == 'range':
                    if cat['min'] <= max_km <= cat['max']:
                        return cat['value']
                elif cat_type == 'range_m':
                    max_m = max_km * 1000.0
                    if cat['min'] <= max_m <= cat['max']:
                        return cat['value']

        # Fallback: keyword matching
        for cat in sport_categories:
            if cat.get('type') == 'keyword':
                keyword = cat['keyword']
                for name in names:
                    if keyword.lower() in name.lower():
                        return cat['value']

        return None

    @staticmethod
    def get_next_distance_category(distances, sport):
        """Get the next distance category above the current one.

        Returns the value of the next category, or None if already at max.
        """
        current = Race.detect_distance_category(distances, sport)
        if current is None:
            return None
        sport_categories = DISTANCE_CATEGORIES.get(sport, [])
        if not sport_categories:
            return None
        for i, cat in enumerate(sport_categories):
            if cat['value'] == current:
                if i + 1 < len(sport_categories):
                    return sport_categories[i + 1]['value']
                return None
        return None

    @staticmethod
    def get_distance_category_label(category_value, sport):
        """Look up human-readable label for a category value in a sport."""
        if not category_value or not sport:
            return None
        sport_categories = DISTANCE_CATEGORIES.get(sport, [])
        for cat in sport_categories:
            if cat['value'] == category_value:
                return cat['label']
        return None

    @staticmethod
    def generate_unique_slug(title):
        slug = Race.title_to_slug(title)
        original_slug = slug
        counter = 2
        while Race.objects.filter(slug=slug).exists():
            slug = f'{original_slug}-{counter}'
            counter += 1
        return slug

    @staticmethod
    def title_to_slug(title):
        slug = re.sub(r'\s+', '-', title.strip())
        slug = re.sub(r'[^\w\-]', '', slug, flags=re.UNICODE)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        return slug.lower()


class Review(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', '쉬움'),
        ('normal', '보통'),
        ('hard', '어려움'),
    ]

    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='reviews')
    nickname = models.CharField(max_length=50, null=True, blank=True)
    rating = models.SmallIntegerField()
    comment = models.CharField(max_length=200)
    completion_time = models.CharField(max_length=20, null=True, blank=True)
    course_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, null=True, blank=True)
    operation_satisfaction = models.SmallIntegerField(null=True, blank=True)
    recommendation_tags = models.JSONField(null=True, blank=True)
    ip_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'race_reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.display_nickname}: {self.rating}star - {self.race}'

    @property
    def display_nickname(self):
        return self.nickname or '익명'


class RacePendingChange(models.Model):
    FIELD_LABELS = {
        'title': '대회명',
        'race_date': '대회일',
        'race_end_date': '대회종료일',
        'start_time': '출발시간',
        'location': '장소',
        'address': '주소',
        'region': '지역',
        'distances': '종목',
        'registration_start': '접수시작일',
        'registration_end': '접수마감일',
        'registration_phases': '접수 단계',
        'official_url': '공식 URL',
        'description': '설명',
        'organizer': '주최',
        'image_path': '대표 이미지',
        'course_image_uploads': '코스 이미지',
        'giveaway_image_uploads': '기념품 이미지',
    }

    STATUS_LABELS = {
        'pending': '대기중',
        'approved': '승인됨',
        'rejected': '거부됨',
    }

    JSON_FIELDS = [
        'distances', 'giveaways', 'course_images', 'giveaway_images',
        'course_image_uploads', 'giveaway_image_uploads', 'registration_phases',
    ]

    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='pending_changes')
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    source = models.CharField(max_length=255, default='crawler')
    status = models.CharField(max_length=20, default='pending')
    reviewed_by = models.CharField(max_length=255, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'race_pending_changes'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.race} - {self.field_label} ({self.status_display})'

    @property
    def field_label(self):
        return self.FIELD_LABELS.get(self.field_name, self.field_name)

    @property
    def status_display(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    def approve(self, reviewed_by=None):
        import json
        race = self.race
        if not race:
            return False
        new_value = self.new_value
        if self.field_name in self.JSON_FIELDS:
            try:
                new_value = json.loads(new_value)
            except (json.JSONDecodeError, TypeError):
                pass
        setattr(race, self.field_name, new_value)
        race.save(update_fields=[self.field_name, 'updated_at'])
        self.status = 'approved'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
        return True

    def reject(self, reviewed_by=None):
        self.status = 'rejected'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
        return True


class DeviceToken(models.Model):
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=10)
    subscribed_sports = models.JSONField(null=True, blank=True)
    subscribed_regions = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'device_tokens'

    def __str__(self):
        return f'{self.platform}: {self.token[:20]}...'


class RaceFavorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='race_favorites',
    )
    race = models.ForeignKey(
        Race,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'race_favorites'
        unique_together = [('user', 'race')]
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f'{self.user_id} -> Race#{self.race_id}'
