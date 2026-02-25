# backend/practice/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PracticeActivityViewSet, ActivitySignUpViewSet

router = DefaultRouter()
router.register(r'activities', PracticeActivityViewSet)
router.register(r'signups', ActivitySignUpViewSet)

urlpatterns = [
    path('', include(router.urls)),
]