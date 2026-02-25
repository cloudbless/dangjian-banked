"""
Django settings for core project.
"""

from pathlib import Path
from datetime import timedelta # 引入时间处理

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-0_z18$1w8+xor$ldw2e#zo$!za=m_tr=kbsm6y^fca3$(g!uo5'

DEBUG = True

ALLOWED_HOSTS = ['*'] # 允许所有主机访问，方便开发

# 指定自定义用户模型
AUTH_USER_MODEL = 'system.UserProfile'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # --- 第三方库 ---
    'rest_framework',
    'corsheaders',            # 1. 跨域插件 (必须有)
    'rest_framework_simplejwt', # JWT认证
    
    # --- 本地应用 ---
    'system',
    'content',
    'learning',
    'practice',
]

MIDDLEWARE = [
    # 2. 【关键修复】跨域中间件必须放在最上面！
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 3. 【关键修复】CORS 跨域配置 (允许前端访问)
CORS_ALLOW_ALL_ORIGINS = True  # 允许所有域名 (开发模式核武器)
CORS_ALLOW_CREDENTIALS = True  # 允许携带凭证

# 允许的请求头
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + [
    'token',
    'authorization',
    'content-type',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'party_platform_db',
        'USER': 'party_user',      
        'PASSWORD': 'party123456', 
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# 4. 【优化】设置为中文环境
LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True # 建议开启，数据库存UTC，显示转本地时间


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# 5. 【新增】媒体文件配置 (用于上传头像、视频)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# REST Framework 配置
REST_FRAMEWORK = {
    # ... 之前的认证配置 ...
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    
    # === 新增：全局分页配置 ===
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,  # 默认每页 10 条
}

# JWT 配置
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1), 
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}
import os

# 静态文件访问路径
MEDIA_URL = '/media/'
# 文件实际存储在硬盘上的路径
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')