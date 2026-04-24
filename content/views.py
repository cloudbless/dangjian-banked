# backend/content/views.py
from django.conf import settings
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from .models import Article
from .serializers import ArticleSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action # 👇 新增引入 action
from rest_framework.response import Response # 👇 新增引入 Response
class ArticleViewSet(viewsets.ModelViewSet):
    # 移除固定的 queryset 属性，完全交由 get_queryset 动态处理
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        根据前端传来的 scope 参数，精准区分门户数据与支部数据
        """
        queryset = Article.objects.all()
        
        # 1. 基础过滤：文章分类
        article_type = self.request.query_params.get('article_type')
        if article_type:
            queryset = queryset.filter(article_type=article_type)

        # 2. 核心隔离：判断前端要的是哪个端的数据
        scope = self.request.query_params.get('scope')

        if scope == 'portal':
            # 【门户端】只展示一级管理员 (super_admin) 发布的数据
            return queryset.filter(author__role='super_admin')
            
        elif scope == 'branch':
            # 【支部端】只展示当前用户所在支部的数据
            user = self.request.user
            if not user.is_authenticated:
                return queryset.none() # 未登录直接返回空
            if user.role in ['branch_admin', 'member']:
                return queryset.filter(organization=user.organization)
            return queryset # 超管能看到所有支部的数据

        # 3. 后台管理端的默认逻辑 (没有传 scope)
        user = self.request.user
        if user.is_authenticated and user.role in ['branch_admin', 'member']:
             return queryset.filter(organization=user.organization)
             
        return queryset
        

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            organization=self.request.user.organization
        )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated]) 
    def like(self, request, pk=None):
        article = self.get_object()
        user = request.user
        
        # 判断如果用户已经点过赞了，就取消点赞
        if article.likes.filter(id=user.id).exists():
            article.likes.remove(user)
            return Response({'status': 'unliked', 'like_count': article.likes.count()})
        # 如果没点过，就加上点赞
        else:
            article.likes.add(user)
            return Response({'status': 'liked', 'like_count': article.likes.count()})
# ... 下面的 upload_editor_image 保持不变 ...
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def upload_editor_image(request):
    if request.method == 'POST':
        file = request.FILES.get('wangeditor-uploaded-image') # WangEditor 默认的文件名
        if file:
            # 保存到 media/editor/ 目录下
            path = default_storage.save(f'editor/{file.name}', file)
            url = f"{settings.MEDIA_URL}{path}"
            # 必须返回 WangEditor 要求的固定格式 JSON
            return JsonResponse({
                "errno": 0,
                "data": {
                    "url": f"http://127.0.0.1:8000{url}", # 注意补全域名
                    "alt": file.name,
                    "href": ""
                }
            })
    return JsonResponse({"errno": 1, "message": "上传失败"})

