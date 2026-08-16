"""Admin-only REST API for inline race editing and image management.

Auth: `Authorization: Bearer <ADMIN_SECRET>`. The SvelteKit `/admin` UI
proxies browser requests through its own server endpoints, validates the
`admin_token` cookie, then forwards here with the bearer header.
크롤러(crawler-worker)도 같은 bearer 인증으로 이 API를 사용한다.
"""
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .image_utils import delete_upload, get_webp_path, process_image, save_upload
from .models import Race
from .serializers import RaceSerializer


class IsAdminBearer(BasePermission):
    message = 'Admin authorization required.'

    def has_permission(self, request, view):
        secret = getattr(settings, 'ADMIN_SECRET', '')
        if not secret:
            return False
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth.startswith('Bearer '):
            return False
        return auth[7:] == secret


EDITABLE_FIELDS = [
    'title', 'slug', 'sport', 'edition',
    'race_date', 'race_end_date', 'start_time',
    'location', 'address', 'latitude', 'longitude', 'region',
    'registration_start', 'registration_end', 'registration_phases',
    'distances', 'giveaways',
    'official_url', 'recap_url', 'ai_summary',
    'status', 'description',
    'organizer', 'organizer_contact', 'organizer_email',
    'course_surface', 'course_difficulty', 'aid_stations', 'timing_method', 'parking',
    'auto_update_enabled', 'locked_fields',
]


class RaceAdminEditSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Race
        fields = EDITABLE_FIELDS
        extra_kwargs = {f: {'required': False} for f in EDITABLE_FIELDS}


def _get_race(slug):
    if slug.isdigit():
        return Race.objects.get(id=int(slug))
    return Race.objects.get(slug=slug)


class RaceAdminListView(APIView):
    authentication_classes = []
    permission_classes = [IsAdminBearer]

    def get(self, request):
        q = (request.query_params.get('q') or '').strip()
        per_page = max(1, min(int(request.query_params.get('per_page') or 50), 200))
        page = max(1, int(request.query_params.get('page') or 1))

        qs = Race.objects.all()
        if q:
            qs = qs.filter(title__icontains=q)

        total = qs.count()
        offset = (page - 1) * per_page
        items = qs.order_by('-race_date')[offset:offset + per_page]

        return Response({
            'races': [
                {
                    'id': r.id,
                    'slug': r.slug,
                    'title': r.title,
                    'sport': r.sport,
                    'sport_label': r.sport_label,
                    'race_date': r.race_date.isoformat() if r.race_date else None,
                    'region': r.region,
                    'location': r.location,
                    'image_src_thumb': r.image_src_thumb,
                    'is_verified': r.is_verified,
                }
                for r in items
            ],
            'total': total,
            'page': page,
            'per_page': per_page,
        })


def _missing_enrich_fields(race):
    """보강(enrich) 크롤러가 채울 수 있는 누락 필드 목록. locked_fields 는 제외."""
    locked = set(race.locked_fields or [])
    missing = []
    if 'distances' not in locked:
        if not Race.distance_names(race.distances):
            missing.append('distances')
        elif not any(isinstance(d, dict) and d.get('fee') is not None
                     for d in race.distances):
            missing.append('fee')
    if not race.giveaways and 'giveaways' not in locked:
        missing.append('giveaways')
    if (not race.course_images and not race.course_image_uploads
            and 'course_images' not in locked):
        missing.append('course_images')
    return missing


class RaceAdminEnrichTargetsView(APIView):
    """보강 크롤러용 — 아직 안 끝났고 URL이 있으며 누락 필드가 있는 대회 목록."""

    authentication_classes = []
    permission_classes = [IsAdminBearer]

    def get(self, request):
        limit = max(1, min(int(request.query_params.get('limit') or 500), 1000))
        today = timezone.localdate()
        not_finished = (
            Q(race_end_date__gte=today) |
            Q(race_end_date__isnull=True, race_date__gte=today)
        )
        has_url = (
            (Q(official_url__isnull=False) & ~Q(official_url='')) |
            (Q(source_url__isnull=False) & ~Q(source_url=''))
        )
        qs = (
            Race.objects.filter(not_finished)
            .filter(has_url)
            .filter(auto_update_enabled=True)
            .order_by('race_date')
        )
        targets = []
        for race in qs.iterator():
            missing = _missing_enrich_fields(race)
            if not missing:
                continue
            targets.append({
                'id': race.id,
                'slug': race.slug,
                'title': race.title,
                'sport': race.sport,
                'sport_label': race.sport_label,
                'race_date': race.race_date.isoformat() if race.race_date else None,
                'official_url': race.official_url,
                'source_url': race.source_url,
                'distances': race.distances,
                'locked_fields': list(race.locked_fields or []),
                'missing': missing,
            })
            if len(targets) >= limit:
                break
        return Response({'targets': targets})


def _admin_payload(race):
    """Race detail plus admin-only image upload paths (not exposed publicly)."""
    data = RaceSerializer(race).data
    data['course_image_uploads'] = _resolve_uploads(race.course_image_uploads)
    data['giveaway_image_uploads'] = _resolve_uploads(race.giveaway_image_uploads)
    data['locked_fields'] = list(race.locked_fields or [])
    data['auto_update_enabled'] = race.auto_update_enabled
    data['crawler_tracked_fields'] = list(Race.CRAWLER_TRACKED_FIELDS)
    return data


def _resolve_uploads(paths):
    paths = paths or []
    return [
        {'path': p, 'url': f"{settings.STORAGE_URL}{get_webp_path(p)}"}
        for p in paths
    ]


class RaceAdminDetailView(APIView):
    authentication_classes = []
    permission_classes = [IsAdminBearer]

    def get(self, request, slug):
        try:
            race = _get_race(slug)
        except Race.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(_admin_payload(race))

    def patch(self, request, slug):
        try:
            race = _get_race(slug)
        except Race.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RaceAdminEditSerializer(race, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        serializer.save()

        # 사용자가 locked_fields 자체를 명시적으로 보내지 않았다면, 이번에 편집한
        # 필드 중 크롤러 추적 대상을 자동으로 보호 처리.
        if 'locked_fields' not in serializer.validated_data:
            edited = list(serializer.validated_data.keys())
            newly_locked = race.lock_fields_for_edit(edited)
            if newly_locked:
                race.save(update_fields=['locked_fields', 'updated_at'])

        race.refresh_from_db()
        return Response(_admin_payload(race))


class RaceAdminImageView(APIView):
    """POST: upload N images. DELETE: remove one by path. PUT: reorder."""

    authentication_classes = []
    permission_classes = [IsAdminBearer]

    KIND_CONFIG = {
        'course': {'field': 'course_image_uploads', 'subdir': 'races/course'},
        'giveaway': {'field': 'giveaway_image_uploads', 'subdir': 'races/giveaway'},
    }

    def _resolve(self, slug, kind):
        try:
            race = _get_race(slug)
        except Race.DoesNotExist:
            return None, None, Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        cfg = self.KIND_CONFIG.get(kind)
        if not cfg:
            return None, None, Response(
                {'errors': {'kind': ['kind must be one of: course, giveaway']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return race, cfg, None

    def post(self, request, slug):
        kind = request.data.get('kind') or request.query_params.get('kind')
        race, cfg, err = self._resolve(slug, kind)
        if err:
            return err

        files = request.FILES.getlist('images')
        if not files:
            return Response(
                {'errors': {'images': ['이미지를 한 개 이상 업로드해주세요.']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if len(files) > 20:
            return Response(
                {'errors': {'images': ['한 번에 최대 20장까지 업로드할 수 있습니다.']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        existing = list(getattr(race, cfg['field']) or [])
        new_paths = []
        for f in files:
            rel = save_upload(f, subdir=cfg['subdir'])
            process_image(rel)
            new_paths.append(rel)

        setattr(race, cfg['field'], existing + new_paths)
        race.save()
        race.refresh_from_db()
        return Response(
            {'images': self._serialize_images(race, cfg)},
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, slug):
        kind = request.query_params.get('kind') or request.data.get('kind')
        path = request.query_params.get('path') or request.data.get('path')
        race, cfg, err = self._resolve(slug, kind)
        if err:
            return err
        if not path:
            return Response(
                {'errors': {'path': ['path is required']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        existing = list(getattr(race, cfg['field']) or [])
        if path not in existing:
            return Response(
                {'errors': {'path': ['Not found in this race.']}},
                status=status.HTTP_404_NOT_FOUND,
            )
        existing.remove(path)
        setattr(race, cfg['field'], existing)
        race.save()
        delete_upload(path)
        race.refresh_from_db()
        return Response({'images': self._serialize_images(race, cfg)})

    def put(self, request, slug):
        kind = request.data.get('kind')
        paths = request.data.get('paths')
        race, cfg, err = self._resolve(slug, kind)
        if err:
            return err
        if not isinstance(paths, list):
            return Response(
                {'errors': {'paths': ['paths must be an array']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        existing = set(getattr(race, cfg['field']) or [])
        if set(paths) != existing:
            return Response(
                {'errors': {'paths': ['paths must contain exactly the existing image paths']}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        setattr(race, cfg['field'], list(paths))
        race.save()
        race.refresh_from_db()
        return Response({'images': self._serialize_images(race, cfg)})

    @staticmethod
    def _serialize_images(race, cfg):
        paths = getattr(race, cfg['field']) or []
        return [
            {'path': p, 'url': f"{settings.STORAGE_URL}{get_webp_path(p)}"}
            for p in paths
        ]
