from django.urls import path

from . import views

urlpatterns = [
    # Posts - list (GET) + create (POST)
    path('posts/', views.PostListCreateView.as_view(), name='post-list-create'),
    path('posts/upload-image/', views.PostInlineImageUploadView.as_view(), name='post-upload-image'),
    path('posts/races/', views.PostAvailableRacesView.as_view(), name='post-available-races'),

    # Post detail (GET) + update (PUT) + delete (DELETE)
    path('posts/<int:pk>/', views.PostDetailUpdateDeleteView.as_view(), name='post-detail'),
    path('posts/<int:pk>/verify-password/', views.PostVerifyPasswordView.as_view(), name='post-verify-password'),

    # Comments - create (POST)
    path('posts/<int:post_id>/comments/', views.CommentCreateView.as_view(), name='comment-create'),
    # Comments - update (PUT) + delete (DELETE)
    path('posts/<int:post_id>/comments/<int:comment_id>/', views.CommentUpdateDeleteView.as_view(), name='comment-update-delete'),

    # Likes
    path('posts/<int:post_id>/like/', views.PostLikeToggleView.as_view(), name='post-like-toggle'),
]
