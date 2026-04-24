# backend/content/serializers.py
from rest_framework import serializers
from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    # 👇 新增这两个动态计算字段
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = '__all__'

    # 获取总点赞数
    def get_like_count(self, obj):
        return obj.likes.count()

    # 获取当前用户是否已点赞
    def get_is_liked(self, obj):
        request = self.context.get('request')
        # 如果用户已登录，判断他是否在 likes 列表里
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False