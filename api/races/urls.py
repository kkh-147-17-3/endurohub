from django.urls import path

from . import admin_api, views

urlpatterns = [
    # Admin (bearer-token, separate from Django admin UI)
    path('admin/races/', admin_api.RaceAdminListView.as_view(), name='admin-race-list'),
    path('admin/races/enrich-targets/', admin_api.RaceAdminEnrichTargetsView.as_view(), name='admin-race-enrich-targets'),
    path('admin/races/<str:slug>/', admin_api.RaceAdminDetailView.as_view(), name='admin-race-detail'),
    path('admin/races/<str:slug>/images/', admin_api.RaceAdminImageView.as_view(), name='admin-race-images'),

    # Home
    path('home/', views.HomeView.as_view(), name='home'),

    # Races
    path('races/', views.RaceListView.as_view(), name='race-list'),
    # 자연어(AI) 대회 검색 — 일단 비활성화. 재활성화하려면 아래 라우트 주석을 해제하세요.
    # path('races/search/', views.RaceNlSearchView.as_view(), name='race-nl-search'),
    path('races/calendar/', views.RaceCalendarView.as_view(), name='race-calendar'),
    path('races/sports/', views.RaceSportsView.as_view(), name='race-sports'),
    path('races/regions/', views.RaceRegionsView.as_view(), name='race-regions'),
    path('races/recommendations/', views.RecommendationsView.as_view(), name='race-recommendations'),
    path('races/year/<int:year>/', views.RaceYearlyView.as_view(), name='race-yearly'),
    path('races/<str:slug>/', views.RaceDetailView.as_view(), name='race-detail'),
    path('races/<str:slug>/reviews/', views.ReviewCreateView.as_view(), name='review-create'),
    path('races/<str:slug>/reviews/<int:review_id>/like/', views.ReviewLikeToggleView.as_view(), name='review-like-toggle'),
    path('races/<str:slug>/favorite/', views.RaceFavoriteToggleView.as_view(), name='race-favorite-toggle'),
    path('races/<str:slug>/images/', views.RaceImageUploadView.as_view(), name='race-image-upload'),

    # Sitemap
    path('sitemap/', views.SitemapView.as_view(), name='sitemap'),

    # Device tokens
    path('devices/', views.DeviceTokenCreateView.as_view(), name='device-create'),
    path('devices/update/', views.DeviceTokenUpdateView.as_view(), name='device-update'),
    path('devices/delete/', views.DeviceTokenDeleteView.as_view(), name='device-delete'),
]
