# backend/core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 引入 JWT 登录视图
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# 记得引入上传函数
from content.views import upload_editor_image 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. 认证接口
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 2. 业务接口
    path('api/system/', include('system.urls')),
    path('api/content/', include('content.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/practice/', include('practice.urls')),

    # 3. 编辑器图片上传接口
    path('api/upload/image/', upload_editor_image),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # 👈 这里已修复