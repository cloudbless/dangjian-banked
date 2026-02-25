from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. 组织架构表 (支持无限层级)
class Organization(models.Model):
    name = models.CharField(max_length=100, verbose_name="组织名称")
    # 自关联，实现树形结构 (例如：党委 -> 总支 -> 支部)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name="上级组织")
    level = models.IntegerField(default=1, verbose_name="层级") # 1:一级, 2:二级...
    description = models.TextField(blank=True, verbose_name="简介")
    
    class Meta:
        verbose_name = "组织架构"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

# 2. 用户扩展表 (继承 Django 自带用户系统)
class UserProfile(AbstractUser):
    # 角色定义
    ROLE_CHOICES = (
        ('super_admin', '一级管理员'),
        ('branch_admin', '支部管理员'),
        ('member', '普通党员'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name="角色")
    # 关联组织 (核心：数据隔离的关键)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name='members', verbose_name="所属组织")
    
    # 个人信息
    phone = models.CharField(max_length=11, blank=True, verbose_name="手机号")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="头像")
    
    # 成长与积分
    total_points = models.IntegerField(default=0, verbose_name="总积分")
    
    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name
# backend/system/models.py

class PointsLog(models.Model):
    """
    积分变动记录表
    """
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='points_logs')
    change_amount = models.IntegerField(verbose_name="变动分值")
    reason = models.CharField(max_length=200, verbose_name="变动原因")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="记录时间")

    class Meta:
        ordering = ['-created_at']