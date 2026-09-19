from typing import Any, cast

from django_filters import rest_framework as filters

from .constants import DISTANCE_CATEGORIES, REGIONS, SPORTS, STATUS_LABELS
from .models import DistanceCategory, Race, RaceQuerySet


SPORT_CHOICES = [(item['value'], item['label']) for item in SPORTS]
REGION_CHOICES = [(r, r) for r in REGIONS]
STATUS_CHOICES = [(k, v) for k, v in STATUS_LABELS.items()] + [('closing_soon', '접수마감임박')]

_DISTANCE_CATEGORY_CHOICES: list[tuple[str, str]] = []
for sport, cats in DISTANCE_CATEGORIES.items():
    for cat in cast("list[DistanceCategory]", cats):
        _DISTANCE_CATEGORY_CHOICES.append((cat['value'], f"{sport}: {cat['label']}"))


class RaceFilter(filters.FilterSet):
    sport = filters.MultipleChoiceFilter(
        choices=SPORT_CHOICES,
        method='filter_sport',
    )
    region = filters.MultipleChoiceFilter(
        choices=REGION_CHOICES,
        method='filter_region',
    )
    status = filters.MultipleChoiceFilter(
        choices=STATUS_CHOICES,
        method='filter_status',
    )
    name = filters.CharFilter(field_name='title', lookup_expr='icontains')
    distance_category = filters.MultipleChoiceFilter(
        choices=_DISTANCE_CATEGORY_CHOICES,
        method='filter_distance_category',
    )
    month_from = filters.CharFilter(method='filter_month_range')
    month_to = filters.CharFilter(method='filter_month_range')
    upcoming = filters.BooleanFilter(method='filter_upcoming')
    closing_soon = filters.BooleanFilter(method='filter_closing_soon')
    days = filters.NumberFilter(method='filter_closing_soon')

    class Meta:
        model = Race
        fields: list[str] = []

    def filter_sport(self, queryset: RaceQuerySet, name: str, value: list[str]) -> RaceQuerySet:
        values = [v for v in value if v]
        if not values:
            return queryset
        return queryset.by_sport(values)

    def filter_region(self, queryset: RaceQuerySet, name: str, value: list[str]) -> RaceQuerySet:
        values = [v for v in value if v]
        if not values:
            return queryset
        return queryset.by_region(values)

    def filter_status(self, queryset: RaceQuerySet, name: str, value: list[str]) -> RaceQuerySet:
        statuses = [v for v in value if v]
        if not statuses:
            return queryset

        has_closing_soon = 'closing_soon' in statuses
        regular_statuses = [s for s in statuses if s != 'closing_soon']

        if has_closing_soon and regular_statuses:
            closing_ids = Race.objects.closing_soon(7).values_list('pk', flat=True)
            status_ids = Race.objects.by_status(regular_statuses).values_list('pk', flat=True)
            return Race.objects.filter(pk__in=set(closing_ids) | set(status_ids))
        if has_closing_soon:
            return Race.objects.closing_soon(7)
        if regular_statuses:
            return queryset.by_status(regular_statuses)
        return queryset

    def filter_month_range(self, queryset: RaceQuerySet, name: str, value: Any) -> RaceQuerySet:
        month_from = self.form.cleaned_data.get('month_from')
        month_to = self.form.cleaned_data.get('month_to')
        return queryset.by_month_range(month_from, month_to)

    def filter_distance_category(self, queryset: RaceQuerySet, name: str, value: list[str]) -> RaceQuerySet:
        categories = [v for v in value if v]
        if not categories:
            return queryset

        sports = self.form.cleaned_data.get('sport') or []
        sports = [s for s in sports if s]
        if len(sports) != 1:
            return queryset

        return queryset.by_distance_category(sports[0], categories)

    def filter_upcoming(self, queryset: RaceQuerySet, name: str, value: bool) -> RaceQuerySet:
        if value:
            return Race.objects.upcoming()
        return queryset

    def filter_closing_soon(self, queryset: RaceQuerySet, name: str, value: Any) -> RaceQuerySet:
        closing_soon = self.form.cleaned_data.get('closing_soon')
        if not closing_soon:
            return queryset
        days = self.form.cleaned_data.get('days') or 7
        return Race.objects.closing_soon(int(days))
