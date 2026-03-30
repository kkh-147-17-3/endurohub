from django.urls import include, path

from .views import EventTrackView

urlpatterns = [
    path('events/', EventTrackView.as_view()),
    path('', include('races.urls')),
    path('', include('posts.urls')),
    path('', include('accounts.urls')),
]
