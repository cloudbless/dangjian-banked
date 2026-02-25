# backend/content/serializers.py
from rest_framework import serializers
from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = Article
        fields = '__all__'
        # 自动把 author 设置为当前登录用户，不需要前端传
        read_only_fields = ['author', 'organization', 'created_at']