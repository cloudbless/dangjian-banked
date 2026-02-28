# backend/system/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, UserViewSet, PointsLogViewSet, dashboard_stats, my_branch_info # 👈 引入新视图

router = DefaultRouter()
router.register(r'orgs', OrganizationViewSet)
router.register(r'users', UserViewSet, basename='user')
router.register(r'points-logs', PointsLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('stats/dashboard/', dashboard_stats),
    path('my_branch/', my_branch_info), # 👈 新增这一行
]