from django.urls import include, path

urlpatterns = [
    path('', include('races.urls')),
    path('', include('posts.urls')),
    path('', include('accounts.urls')),
]
