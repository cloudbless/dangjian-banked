# backend/practice/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import PracticeActivity, ActivitySignUp
from .serializers import PracticeActivitySerializer, ActivitySignUpSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from system.models import PointsLog
from django.db.models import Q # 引入 Q 查询

class PracticeActivityViewSet(viewsets.ModelViewSet):
    queryset = PracticeActivity.objects.all()
    serializer_class = PracticeActivitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = PracticeActivity.objects.all().order_by('-created_at')
        
        scope = self.request.query_params.get('scope')

        if scope == 'portal':
            # 【门户端】只看一级管理员发布的活动
            return queryset.filter(publisher__role='super_admin')
            
        elif scope == 'branch':
            # 【支部端】只看本支部发布的活动
            user = self.request.user
            if not user.is_authenticated:
                return queryset.none()
            if user.role in ['branch_admin', 'member']:
                return queryset.filter(organization=user.organization)
            return queryset

        # 【后台管理端】默认逻辑
        user = self.request.user
        if user.is_authenticated and user.role in ['branch_admin', 'member']:
             return queryset.filter(organization=user.organization)
             
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            publisher=self.request.user,
            organization=self.request.user.organization
        )

# ... 下面的 ActivitySignUpViewSet 保持不变 ...

class ActivitySignUpViewSet(viewsets.ModelViewSet):
    queryset = ActivitySignUp.objects.all()
    serializer_class = ActivitySignUpSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        try:
            # 尝试保存报名记录
            serializer.save(user=self.request.user)
        except IntegrityError:
            # 如果触发了数据库的唯一约束（重复报名），抛出 400 错误
            raise ValidationError({'detail': '您已经报名过该活动，请勿重复操作！'})

    # === 把下面这段加回来：审核签到并发放积分的专属接口 ===
    @action(detail=True, methods=['post'])
    def confirm_attendance(self, request, pk=None):
        signup_record = self.get_object()
        
        # 1. 防止重复发积分
        if signup_record.status == 3:
            return Response({'error': '该党员已签到并获取过积分'}, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. 把报名状态改成 "3 (已签到)"
        signup_record.status = 3
        signup_record.save()
        
        # 3. 核心逻辑：找到这个党员，给他加上这活的奖励积分！
        user = signup_record.user
        points = signup_record.activity.points_reward
        user.total_points += points
        user.save()
        
        # 新增：记录积分轨迹
        PointsLog.objects.create(
            user=user,
            change_amount=points,
            reason=f"参加实践活动：{signup_record.activity.title}"
        )
        
        return Response({
            'status': 'success', 
            'message': f'已确认签到，成功为 {user.username} 发放 {signup_record.activity.points_reward} 积分！'
        })