# backend/learning/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import Course, StudyRecord, Question
from .serializers import CourseSerializer, StudyRecordSerializer, QuestionSerializer
from system.models import PointsLog
from django.db.models import Q # 👇 引入 Q 查询，用于多条件过滤

class CourseViewSet(viewsets.ModelViewSet):
    # 👇 保留 queryset 属性，防止 router 报错
    queryset = Course.objects.all().order_by('-created_at') 
    serializer_class = CourseSerializer
    
    # 允许门户端未登录用户查看公开课
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Course.objects.all().order_by('-created_at')
        scope = self.request.query_params.get('scope')
        user = self.request.user

        # === 1. 基础数据隔离 ===
        if scope == 'portal':
            queryset = queryset.filter(publisher__role='super_admin')
        elif scope == 'branch':
            if not user.is_authenticated:
                return queryset.none()
            if user.role in ['branch_admin', 'member']:
                queryset = queryset.filter(Q(organization=user.organization) | Q(organization__isnull=True))
        else:
            # 个人中心默认逻辑：放宽范围
            if user.is_authenticated and user.role in ['branch_admin', 'member']:
                 queryset = queryset.filter(Q(organization=user.organization) | Q(publisher__role='super_admin') | Q(organization__isnull=True))

        # === 2. 必修课过滤 (处理 is_required) ===
        is_required_param = self.request.query_params.get('is_required')
        is_req = None
        if is_required_param is not None:
            is_req = is_required_param.lower() in ['true', '1']
            queryset = queryset.filter(is_required=is_req)

        # === 3. 完成状态过滤 (处理 is_completed) ===
        is_completed_param = self.request.query_params.get('is_completed')
        if is_completed_param is not None and user.is_authenticated:
            is_comp = is_completed_param.lower() in ['true', '1']
            
            # 获取当前用户实打实已完成的课程 ID 列表
            completed_course_ids = StudyRecord.objects.filter(
                user=user, 
                is_completed=True
            ).values_list('course_id', flat=True)

            if is_comp:
                # 【核心修复】：如果是查“已完成”，解除组织隔离！直接从全库中匹配他学过的课
                queryset = Course.objects.filter(id__in=completed_course_ids)
                # 补回必修过滤条件
                if is_req is not None:
                    queryset = queryset.filter(is_required=is_req)
            else:
                # 如果是查“待完成”，从刚才隔离好的列表中排除掉已经学完的
                queryset = queryset.exclude(id__in=completed_course_ids)

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
            type_name = course.get_course_type_display() if hasattr(course, 'get_course_type_display') else "课程"
            # 2. 记录积分轨迹 (写入明细表)
            PointsLog.objects.create(
            user=user,
            change_amount=course.points_reward,
            reason=f"完成{type_name}学习：{course.title}"  # 👈 这样就会显示 "完成图文学习：xxx" 或 "完成视频学习：xxx"
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
    @action(detail=False, methods=['get'])
    def branch_stats(self, request):
        from system.models import UserProfile 
        from .models import Course, StudyRecord # 确保引入 Course
        from django.db.models import Q # 确保引入 Q
        
        user = request.user
        org_id = request.query_params.get('org_id')

        # 1. 权限与数据范围判定
        if user.role == 'super_admin':
            if org_id:
                users = UserProfile.objects.filter(organization_id=org_id)
            else:
                users = UserProfile.objects.all()
        elif user.role == 'branch_admin':
            users = UserProfile.objects.filter(organization=user.organization)
        else:
            return Response({'error': '无权限查看'}, status=403)

        # 2. 组装每个人的学习数据
        data = []
        for u in users:
            # 👇 新增：计算该党员应该完成的“必修课总数” (包含超管发的、本支部发的、全局公开的)
            required_count = Course.objects.filter(
                Q(organization=u.organization) | Q(publisher__role='super_admin') | Q(organization__isnull=True),
                is_required=True
            ).distinct().count()

            records = StudyRecord.objects.filter(user=u).select_related('course')
            record_data = []
            completed_required = 0 # 👇 新增：统计该党员已完成的必修课数量

            for r in records:
                is_req = r.course.is_required
                # 如果这门课是必修，且状态是已完成，则计数 + 1
                if is_req and r.is_completed:
                    completed_required += 1

                record_data.append({
                    'course_id': r.course.id,
                    'course_title': r.course.title,
                    'is_completed': r.is_completed,
                    'is_required': is_req,
                    'progress': r.progress,
                    'last_studied_at': r.last_studied_at.strftime('%Y-%m-%d %H:%M') if r.last_studied_at else None,
                })
            
            data.append({
                'user_id': u.id,
                'username': u.username,
                'total_points': u.total_points,
                'organization_name': u.organization.name if u.organization else '未分配',
                'required_count': required_count,           # 传给前端：必修总数
                'completed_required': completed_required,   # 传给前端：已完成必修数
                'records': record_data
            })

        return Response(data)
# 👇 新增题目视图
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().order_by('id')
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        # 允许通过 course_id 过滤某节课的题目
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset