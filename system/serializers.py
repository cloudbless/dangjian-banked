# backend/system/serializers.py

from rest_framework import serializers
from .models import UserProfile, Organization, PointsLog, PartyMemberRecord

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

# 👇 1. 新增档案的序列化器
class PartyMemberRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyMemberRecord
        exclude = ('id', 'user') # 不需要返回主键和外键，只需核心数据
        
# 👇 2. 修改原有的 UserProfileSerializer
class UserProfileSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'real_name', 'gender', 'join_party_date', 
            'birthday', 'identity_card', 'role', 'organization', 
            'organization_name', 'phone', 'avatar', 'total_points'
        ]

    # 巧妙的聚合：在返回数据前，把纪实档案合并进去
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # 如果存在纪实档案记录，直接将其拍平(merge)到 user_data 中
        if hasattr(instance, 'development_record'):
            record_data = PartyMemberRecordSerializer(instance.development_record).data
            data.update(record_data)
        return data