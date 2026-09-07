from django.urls import path

from . import views

urlpatterns = [
    path('notices/', views.NoticeListView.as_view(), name='notice-list'),
    path('notices/by-slug/<slug:slug>/', views.NoticeSlugDetailView.as_view(), name='notice-slug-detail'),
    path('notices/<int:notice_id>/comments/', views.NoticeCommentCreateView.as_view(), name='notice-comment-create'),
    path('notices/<int:notice_id>/comments/<int:comment_id>/', views.NoticeCommentUpdateDeleteView.as_view(), name='notice-comment-update-delete'),
    path('notices/<int:pk>/', views.NoticeDetailView.as_view(), name='notice-detail'),
    path('popups/active/', views.PopupActiveView.as_view(), name='popup-active'),
]
