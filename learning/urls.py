# backend/learning/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, StudyRecordViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'records', StudyRecordViewSet, basename='studyrecord')

urlpatterns = [
    path('', include(router.urls)),
]