from django.urls import path

from . import views

urlpatterns = [
    path('auth/<str:provider>/login/', views.OAuthLoginView.as_view()),
    path('auth/<str:provider>/callback/', views.OAuthCallbackView.as_view()),
    path('auth/nickname/', views.NicknameSetupView.as_view()),
    path('auth/email/send/', views.EmailSendView.as_view()),
    path('auth/email/verify/', views.EmailVerifyView.as_view()),
    path('auth/pending/email/send/', views.PendingSocialEmailSendView.as_view()),
    path('auth/pending/email/verify/', views.PendingSocialEmailVerifyView.as_view()),
    path('auth/me/', views.MeView.as_view()),
    path('auth/preferences/', views.ProfilePreferencesView.as_view()),
    path('auth/onboarding/', views.OnboardingView.as_view()),
    path('auth/logout/', views.LogoutView.as_view()),
    path('me/favorites/races/', views.MyFavoriteRacesView.as_view()),
]
