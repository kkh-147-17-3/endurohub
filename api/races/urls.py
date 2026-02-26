from django.urls import path

from . import views

urlpatterns = [
    # Home
    path('home/', views.HomeView.as_view(), name='home'),

    # Races
    path('races/', views.RaceListView.as_view(), name='race-list'),
    path('races/calendar/', views.RaceCalendarView.as_view(), name='race-calendar'),
    path('races/sports/', views.RaceSportsView.as_view(), name='race-sports'),
    path('races/regions/', views.RaceRegionsView.as_view(), name='race-regions'),
    path('races/year/<int:year>/', views.RaceYearlyView.as_view(), name='race-yearly'),
    path('races/<str:slug>/', views.RaceDetailView.as_view(), name='race-detail'),
    path('races/<str:slug>/reviews/', views.ReviewCreateView.as_view(), name='review-create'),
    path('races/<str:slug>/images/', views.RaceImageUploadView.as_view(), name='race-image-upload'),

    # Sitemap
    path('sitemap/', views.SitemapView.as_view(), name='sitemap'),

    # Device tokens
    path('devices/', views.DeviceTokenCreateView.as_view(), name='device-create'),
    path('devices/update/', views.DeviceTokenUpdateView.as_view(), name='device-update'),
    path('devices/delete/', views.DeviceTokenDeleteView.as_view(), name='device-delete'),
]
