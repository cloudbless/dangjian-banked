# backend/learning/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, QuestionViewSet, StudyRecordViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'records', StudyRecordViewSet, basename='studyrecord')
router.register(r'questions', QuestionViewSet) # 👇 注册新路由
urlpatterns = [
    path('', include(router.urls)),
]