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
    # 显示组织的名称，而不是只有ID
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = UserProfile
        # 千万不要把 password 返回给前端！
        fields = ['id', 'username', 'first_name', 'role', 'organization', 'organization_name', 'phone', 'avatar', 'total_points']