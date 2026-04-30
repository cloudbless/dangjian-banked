# backend/system/serializers.py

from rest_framework import serializers
from .models import Organization, UserProfile

# 1. 组织架构序列化
class OrganizationSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField() # 递归获取子部门

    class Meta:
        model = Organization
        fields = '__all__'

    def get_children(self, obj):
        # 这是一个递归，用于生成树形结构
        if obj.children.exists():
            return OrganizationSerializer(obj.children.all(), many=True).data
        return []

# 2. 用户信息序列化
class UserProfileSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = UserProfile
        # 👇 在 fields 中加入新增的字段
        fields = [
            'id', 'username', 'real_name', 'gender', 'join_party_date', 
            'birthday', 'identity_card', 'role', 'organization', 
            'organization_name', 'phone', 'avatar', 'total_points'
        ]