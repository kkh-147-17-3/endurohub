from django.urls import path

from . import views

urlpatterns = [
    path('notices/', views.NoticeListView.as_view(), name='notice-list'),
    path('notices/<int:pk>/', views.NoticeDetailView.as_view(), name='notice-detail'),
]
