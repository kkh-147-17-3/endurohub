from django.urls import path

from .views import CoffeeCouponEventStatusView


urlpatterns = [
    path('rewards/coffee-coupon-event/status/', CoffeeCouponEventStatusView.as_view()),
]
