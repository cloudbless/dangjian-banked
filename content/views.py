# backend/content/views.py
from django.conf import settings
from rest_framework import viewsets
# 引入权限类
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Article
from .serializers import ArticleSerializer

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    # 允许未登录用户阅读 (GET)，修改 (POST/PUT) 必须登录
    permission_classes = [IsAuthenticatedOrReadOnly]

    # === 关键：实现分类过滤逻辑 ===
    def get_queryset(self):
        """
        根据 URL 传参进行过滤，例如：/api/content/articles/?article_type=1
        """
        queryset = Article.objects.all()
        # 获取前端传来的 article_type 参数
        article_type = self.request.query_params.get('article_type')
        
        if article_type:
            queryset = queryset.filter(article_type=article_type)
            
        return queryset

    # === 保持你原有的自动填充逻辑 ===
    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            organization=self.request.user.organization
        )
        # backend/content/views.py
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