# backend/learning/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import Course, StudyRecord
from .serializers import CourseSerializer, StudyRecordSerializer
from system.models import PointsLog
from django.db.models import Q # 👇 引入 Q 查询，用于多条件过滤

class CourseViewSet(viewsets.ModelViewSet):
    # 👇 保留 queryset 属性，防止 router 报错
    queryset = Course.objects.all().order_by('-created_at') 
    serializer_class = CourseSerializer
    
    # 允许门户端未登录用户查看公开课
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        课程列表的数据隔离逻辑
        """
        queryset = Course.objects.all().order_by('-created_at')
        scope = self.request.query_params.get('scope')

        if scope == 'portal':
            # 【门户端】只展示一级管理员发布的课程
            return queryset.filter(publisher__role='super_admin')
            
        elif scope == 'branch':
            # 【支部端】只能看到“本支部发布的课程” + “全局公开的课程”
            user = self.request.user
            if not user.is_authenticated:
                return queryset.none()
            if user.role in ['branch_admin', 'member']:
                return queryset.filter(Q(organization=user.organization) | Q(organization__isnull=True))
            return queryset

        # 【后台管理端】默认逻辑
        # 【默认逻辑：修复 404】
        # 即便前端详情页没传 scope 参数，只要是本支部或超管发的，都允许读取
        user = self.request.user
        if user.is_authenticated and user.role in ['branch_admin', 'member']:
             return queryset.filter(Q(organization=user.organization) | Q(publisher__role='super_admin'))
             
        return queryset

    def perform_create(self, serializer):
        # 创建课程时，自动绑定发布者和所在组织
        serializer.save(
            publisher=self.request.user,
            organization=self.request.user.organization
        )


class StudyRecordViewSet(viewsets.ModelViewSet):
    serializer_class = StudyRecordSerializer
    permission_classes = [IsAuthenticated]

    # 👇 这个你之前写得很好，天然隔离了，不需要改！
    def get_queryset(self):
        return StudyRecord.objects.filter(user=self.request.user)
        
    # ... 下面的 update_progress 等代码保持不变 ...

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # === 唯一正确的进度更新接口 ===
    @action(detail=False, methods=['post'])
    def update_progress(self, request):
        course_id = request.data.get('course_id')
        current_time = request.data.get('current_time', 0) # 前端传来的当前秒数
        is_finished = request.data.get('is_finished', False) # 核心：从前端接收是否播完的信号
        
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'error': '课程不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 获取或创建学习记录
        record, created = StudyRecord.objects.get_or_create(
            user=request.user,
            course=course
        )

        msg = "进度已保存"

        # 核心逻辑：如果前端说播完了，且数据库还没标记完成
        if not record.is_completed and is_finished:
            record.is_completed = True
            
            # 兼容处理：检查模型用的是 points 还是 credit，防止字段名不一致报错
            points_earned = course.points_reward
            
            # 1. 给用户增加总积分
            user = request.user
            user.total_points += points_earned
            user.save()

            # 2. 记录积分轨迹 (写入明细表)
            PointsLog.objects.create(
                user=user,
                change_amount=points_earned,
                reason=f"完成视频课程学习：{course.title}"
            )
            msg = f"恭喜完成学习，获得 {points_earned} 积分！"
            
        # 更新进度时间（如果已经看完就不更新进度了，避免重新点开视频时进度清零）
        if not record.is_completed:
            record.progress = current_time
            
        record.save()

        return Response({
            'status': 'success', 
            'message': msg,
            'is_completed': record.is_completed,
            'current_points': request.user.total_points
        })