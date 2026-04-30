# backend/practice/serializers.py
from rest_framework import serializers
from .models import PracticeActivity, ActivitySignUp

# backend/practice/serializers.py
class PracticeActivitySerializer(serializers.ModelSerializer):
    publisher_name = serializers.CharField(source='publisher.username', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    current_signups = serializers.SerializerMethodField()
    # 👇 新增字段：是否已报名
    is_registered = serializers.SerializerMethodField() 
    registration_status = serializers.SerializerMethodField()
    class Meta:
        model = PracticeActivity
        fields = '__all__'
        read_only_fields = ['publisher', 'organization']

    def get_current_signups(self, obj):
        return obj.signups.filter(status__in=[0, 1, 3]).count()

    # 👇 新增方法：判断当前用户是否已在此活动报名表中
    def get_is_registered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ActivitySignUp.objects.filter(activity=obj, user=request.user).exists()
        return False
    
    def get_registration_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # 导入 ActivitySignUp (如果文件顶部没导入的话记得加上: from .models import ActivitySignUp)
            signup = ActivitySignUp.objects.filter(activity=obj, user=request.user).first()
            if signup:
                return signup.status # 返回 0, 1, 2, 3
        return -1 # 未报名返回 -1
class ActivitySignUpSerializer(serializers.ModelSerializer):
    activity_title = serializers.CharField(source='activity.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = ActivitySignUp
        fields = '__all__'
        read_only_fields = ['user']