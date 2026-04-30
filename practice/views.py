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
    #核心新增：取消报名接口
    @action(detail=True, methods=['post'])
    def cancel_signup(self, request, pk=None):
        activity = self.get_object()
        
        # 1. 查找当前用户针对该活动的报名记录
        signup = ActivitySignUp.objects.filter(activity=activity, user=request.user).first()
        if not signup:
            return Response({'error': '未找到您的报名记录'}, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. 安全校验：如果报名已经“已通过(1)”或“已发分(3)”，则不允许私自取消
        if signup.status in [1, 3]:
            return Response(
                {'error': '您的报名已通过审核或活动已结束，无法直接取消。如需请假请联系支部书记。'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 3. 删除报名记录
        signup.delete()
        return Response({'message': '已成功取消报名'})



class ActivitySignUpViewSet(viewsets.ModelViewSet):
    queryset = ActivitySignUp.objects.all()
    serializer_class = ActivitySignUpSerializer
    permission_classes = [IsAuthenticated]

    # 👇 核心修复 1：根据前端传来的 activity ID 过滤报名列表，解决后台抽屉显示所有人的问题
    def get_queryset(self):
        queryset = super().get_queryset()
        activity_id = self.request.query_params.get('activity')
        if activity_id:
            queryset = queryset.filter(activity_id=activity_id)
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        try:
            # 尝试保存报名记录
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError({'detail': '您已经报名过该活动，请勿重复操作！'})

    # 👇 核心修复 2：个人中心需要的“我的实践”接口
    @action(detail=False, methods=['get'])
    def my(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "请先登录"}, status=401)
        queryset = self.get_queryset().filter(user=request.user).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # backend/practice/views.py

    @action(detail=True, methods=['post'])
    def audit(self, request, pk=None):
        record = self.get_object()
        new_status = request.data.get('status')
        
        # 🛡️ 安全检查：如果已经发放了积分，绝对不允许撤回审核
        if record.status == 3:
            return Response({'error': '该党员已完成活动并发放积分，无法撤回审核状态'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 👇 允许的状态码增加 0 (重置为待审核)
        if new_status in [0, 1, 2]: # 0: 撤回/待审核, 1: 通过, 2: 驳回
            record.status = new_status
            record.save()
            return Response({'message': '操作成功'})
            
        return Response({'error': '无效的状态码'}, status=status.HTTP_400_BAD_REQUEST)

    # 👇 核心修复 4：后台管理需要的“结项发分”动作
    @action(detail=True, methods=['post'])
    def grant_points(self, request, pk=None):
        signup_record = self.get_object()
        
        # 1. 防止重复发积分
        if signup_record.status == 3:
            return Response({'error': '已发放过积分，请勿重复操作'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. 只有审核通过的才能发分
        if signup_record.status != 1:
            return Response({'error': '仅对审核已通过的党员发放积分'}, status=status.HTTP_400_BAD_REQUEST)
            
        # 3. 把报名状态改成 "3 (已发分)"
        signup_record.status = 3
        signup_record.save()
        
        # 4. 找到党员并加分
        user = signup_record.user
        points = signup_record.activity.points_reward
        user.total_points += points
        user.save()
        
        # 5. 记录积分轨迹
        PointsLog.objects.create(
            user=user,
            change_amount=points,
            reason=f"完成实践活动：{signup_record.activity.title}"
        )
        
        return Response({'message': f'成功发放 {points} 积分！'})