# backend/system/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, UserViewSet, PointsLogViewSet, dashboard_stats # 确保导入了 PointsLogViewSet

router = DefaultRouter()

# 1. 注册组织架构
router.register(r'orgs', OrganizationViewSet)

# 2. 注册用户（手动指定 basename）
router.register(r'users', UserViewSet, basename='user') 

# 3. 注册积分记录（新增）
router.register(r'points-logs', PointsLogViewSet)

urlpatterns = [
    # 将 router 注册的所有 URL 包含进来
    path('', include(router.urls)),
    # 👇 大屏数据路由
    path('stats/dashboard/', dashboard_stats, name='dashboard_stats'),
]