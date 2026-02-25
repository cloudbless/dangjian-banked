from rest_framework import viewsets, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count, Sum

from .models import Organization, UserProfile, PointsLog
from .serializers import OrganizationSerializer, UserProfileSerializer
from learning.models import StudyRecord

# ==========================================
# 权限控制 (RBAC)
# ==========================================
class IsBranchAdminOrHigher(IsAuthenticated):
    """
    仅允许超级管理员或支部管理员访问
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.user.is_superuser:
            return True
        # 角色字段对应：super_admin(一级), branch_admin(支部)
        return request.user.role in ['branch_admin', 'super_admin']

# ==========================================
# 视图集 (ViewSets)
# ==========================================

class OrganizationViewSet(viewsets.ModelViewSet):
    """组织架构管理接口"""
    queryset = Organization.objects.all().order_by('id')
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None 

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # 仅返回一级组织，由 Serializer 递归处理子组织
        root_orgs = queryset.filter(level=1)
        serializer = self.get_serializer(root_orgs, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """用户管理接口 (核心业务逻辑)"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsBranchAdminOrHigher] 

    def get_queryset(self):
        user = self.request.user
        # 统一增加 -id 排序，解决分页警告
        base_qs = UserProfile.objects.all().order_by('-id')
        
        if user.is_superuser or user.role == 'super_admin':
            return base_qs
        
        # 支部管理员数据隔离：只能看到本组织成员
        if user.role == 'branch_admin':
            return base_qs.filter(organization=user.organization)
            
        # 普通用户只能看到自己
        return base_qs.filter(id=user.id)

   # 🎯 核心修复：在这里显式指定，me 接口只需要登录即可，不需要管理员权限
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    # 🎯 重置党员密码
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        target_user = self.get_object()
        new_password = request.data.get('password')
        
        if not new_password:
            return Response({'detail': '请输入新密码'}, status=status.HTTP_400_BAD_REQUEST)
            
        # 权限二层加固
        current_user = request.user
        if current_user.role == 'branch_admin' and target_user.organization != current_user.organization:
            raise PermissionDenied("越权操作：您无权重置其他支部成员密码")

        target_user.set_password(new_password)
        target_user.save()
        return Response({'detail': f'用户 [{target_user.username}] 密码重置成功'})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("❌ 校验失败详情:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'branch_admin':
            incoming_role = serializer.validated_data.get('role', 'user')
            if incoming_role == 'super_admin':
                raise PermissionDenied("权限不足：支部管理员无法创建一级管理员")
            # 强制绑定新党员到管理员所属组织
            serializer.save(organization=user.organization)
        else:
            serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        target_user = self.get_object()
        
        if user.role == 'branch_admin':
            # 防止跨支部修改
            if target_user.organization != user.organization:
                raise PermissionDenied("权限不足：无法修改其他支部成员")
            # 防止越权提权
            incoming_role = serializer.validated_data.get('role', target_user.role)
            if incoming_role == 'super_admin':
                raise PermissionDenied("权限不足：无法授予一级管理员权限")
            # 禁止将人调离本支部
            incoming_org = serializer.validated_data.get('organization', target_user.organization)
            if incoming_org != user.organization:
                raise PermissionDenied("权限不足：无法将成员移出本支部")
                
        serializer.save()

class PointsLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsLog
        fields = '__all__'

class PointsLogViewSet(viewsets.ReadOnlyModelViewSet):
    """积分日志接口"""
    queryset = PointsLog.objects.all().order_by('-created_at')
    serializer_class = PointsLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

# ==========================================
# 大屏数据统计接口 (FBV)
# ==========================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """获取后台首页大屏的所有统计数据"""
    # 基础统计
    total_users = UserProfile.objects.count()
    total_orgs = Organization.objects.count()
    total_studies = StudyRecord.objects.filter(is_completed=True).count()
    
    total_points_dict = UserProfile.objects.aggregate(Sum('total_points'))
    total_points = total_points_dict['total_points__sum'] or 0

    # 饼图：各支部人数分布
    org_users = UserProfile.objects.values('organization__name').annotate(value=Count('id'))
    pie_data = [
        {"name": item['organization__name'] or '未分配支部', "value": item['value']}
        for item in org_users
    ]

    # 柱状图：积分排名前 5 的支部
    org_activity = UserProfile.objects.values('organization__name').annotate(
        active_score=Sum('total_points')
    ).order_by('-active_score')[:5]
    
    bar_x = [item['organization__name'] or '未分配支部' for item in org_activity]
    bar_y = [item['active_score'] or 0 for item in org_activity]

    return Response({
        "cards": {
            "total_users": total_users,
            "total_orgs": total_orgs,
            "total_studies": total_studies,
            "total_points": total_points
        },
        "pie_data": pie_data,
        "bar_data": {
            "categories": bar_x,
            "values": bar_y
        }
    })