# backend/practice/serializers.py
from rest_framework import serializers
from .models import PracticeActivity, ActivitySignUp

class PracticeActivitySerializer(serializers.ModelSerializer):
    publisher_name = serializers.CharField(source='publisher.username', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    current_signups = serializers.SerializerMethodField()

    class Meta:
        model = PracticeActivity
        fields = '__all__'
        read_only_fields = ['publisher', 'organization']

    def get_current_signups(self, obj):
        # 统计有效报名人数
        return obj.signups.filter(status__in=[0, 1, 3]).count()

class ActivitySignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivitySignUp
        fields = '__all__'
        read_only_fields = ['user']