# backend/content/models.py
from django.db import models
from system.models import UserProfile, Organization

class Article(models.Model):
    TYPE_CHOICES = (
        (1, '时政要闻'),
        (2, '通知公告'),
        (3, '党员风采'),
        (4, '支部动态'),
        (5, '学习园地'), # 👈 新增：作为图文展示的学习资料
        (6, '实践中心'), # 👈 新增：作为图文展示的实践活动宣传
    )
    STATUS_CHOICES = (
        (0, '草稿'),
        (1, '已发布'),
    )

    title = models.CharField(max_length=200, verbose_name="标题")
    # 封面图：会自动上传到 media/covers/ 目录
    cover = models.ImageField(upload_to='covers/', null=True, blank=True, verbose_name="封面")
    # 核心内容：存储 HTML 代码
    content = models.TextField(verbose_name="内容")
    
    article_type = models.IntegerField(choices=TYPE_CHOICES, default=1, verbose_name="类型")
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="状态")
    
    # 发布人与发布组织 (用于数据隔离)
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="发布人")
    # 只有本支部的人能看到本支部的通知
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, verbose_name="所属组织")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        ordering = ['-created_at'] # 最新发布的在最前面
        verbose_name = "文章管理"