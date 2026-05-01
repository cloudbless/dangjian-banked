from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
# 1. 组织架构表 (支持无限层级)
class Organization(models.Model):
    name = models.CharField(max_length=100, verbose_name="组织名称")
    # 自关联，实现树形结构 (例如：党委 -> 总支 -> 支部)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name="上级组织")
    level = models.IntegerField(default=1, verbose_name="层级") # 1:一级, 2:二级...
    description = models.TextField(blank=True, verbose_name="简介")
    
    class Meta:
        verbose_name = "组织架构"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

# 2. 用户扩展表 (继承 Django 自带用户系统)
class UserProfile(AbstractUser):
    # 角色定义
    ROLE_CHOICES = (
        ('super_admin', '一级管理员'),
        ('branch_admin', '支部管理员'),
        ('member', '普通党员'),
        ('probationary_member', '预备党员'), # 👇 新增：预备党员角色
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name="角色")
    # 关联组织 (核心：数据隔离的关键)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name='members', verbose_name="所属组织")
    
    # 个人信息
    phone = models.CharField(max_length=11, blank=True, verbose_name="手机号")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="头像")
    
    # 成长与积分
    total_points = models.IntegerField(default=0, verbose_name="总积分")
    
    GENDER_CHOICES = ((1, '男'), (2, '女'))
    real_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="真实姓名")
    gender = models.IntegerField(choices=GENDER_CHOICES, default=1, verbose_name="性别")
    join_party_date = models.DateField(null=True, blank=True, verbose_name="入党时间")
    birthday = models.DateField(null=True, blank=True, verbose_name="出生日期")
    identity_card = models.CharField(max_length=18, null=True, blank=True, verbose_name="身份证号")

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name
# backend/system/models.py

class PointsLog(models.Model):
    """
    积分变动记录表
    """
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='points_logs')
    change_amount = models.IntegerField(verbose_name="变动分值")
    reason = models.CharField(max_length=200, verbose_name="变动原因")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="记录时间")

    class Meta:
        ordering = ['-created_at']

class PartyMemberRecord(models.Model):
    """党员发展纪实档案表"""
    # 一对一绑定用户
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='development_record', verbose_name="关联党员")

    # 一、 基础信息 (原有性别、电话等复用 UserProfile)
    nation = models.CharField(max_length=20, null=True, blank=True, verbose_name="民族")
    native_place = models.CharField(max_length=100, null=True, blank=True, verbose_name="籍贯")
    class_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="班级/部门")

    # 二、 申请入党
    app_submit_time = models.DateField(null=True, blank=True, verbose_name="递交入党申请书时间")
    app_talk_time = models.DateField(null=True, blank=True, verbose_name="党组织派人谈话时间")
    app_talker = models.CharField(max_length=50, null=True, blank=True, verbose_name="谈话人")

    # 三、 入党积极分子的确定和培养教育
    activist_recommend_time = models.DateField(null=True, blank=True, verbose_name="优团/党员推荐时间")
    activist_recommend_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name="推荐情况")
    activist_confirm_time = models.DateField(null=True, blank=True, verbose_name="确定为积极分子时间")
    activist_vote_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name="表决情况")
    activist_public_time = models.DateField(null=True, blank=True, verbose_name="公示时间")
    activist_public_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name="公示情况")
    activist_approve_opinion = models.CharField(max_length=255, null=True, blank=True, verbose_name="上级党委审批意见")
    activist_approve_time = models.DateField(null=True, blank=True, verbose_name="审批时间")

    # 四、 培养联系人
    contact1_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="培养联系人1姓名")
    contact1_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="培养联系人1电话")
    contact2_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="培养联系人2姓名")
    contact2_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="培养联系人2电话")

    # 五、 发展对象的确定和考察
    target_mass_meeting_time = models.DateField(null=True, blank=True, verbose_name="征求群众意见座谈会时间")
    confirm_target_meeting_time = models.DateField(null=True, blank=True, verbose_name="支委会/大会讨论时间")
    target_public_time = models.DateField(null=True, blank=True, verbose_name="公示时间")
    target_public_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name="公示情况")
    target_approve_opinion = models.CharField(max_length=255, null=True, blank=True, verbose_name="上级党委审批意见")
    target_approve_time = models.DateField(null=True, blank=True, verbose_name="审批时间")
    target_train_time = models.DateField(null=True, blank=True, verbose_name="发展对象培训时间")
    target_pol_check = models.CharField(max_length=20, choices=(('合格', '合格'), ('不合格', '不合格')), null=True, blank=True, verbose_name="政审情况")

    # 六、 预备党员的接收
    probation_pre_check_time = models.DateField(null=True, blank=True, verbose_name="上级党委预审时间")
    probation_train_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name="培训情况")
    probation_public_time = models.DateField(null=True, blank=True, verbose_name="拟接收公示时间")
    probation_public_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name="公示情况")
    probation_meeting_time = models.DateField(null=True, blank=True, verbose_name="大会讨论接收时间")
    probation_vote_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name="表决情况")
    probation_talk_time = models.DateField(null=True, blank=True, verbose_name="上级派人谈话时间")
    probation_talker = models.CharField(max_length=50, null=True, blank=True, verbose_name="谈话人")
    probation_approve_opinion = models.CharField(max_length=255, null=True, blank=True, verbose_name="上级党委审批意见")
    probation_approve_time = models.DateField(null=True, blank=True, verbose_name="审批时间")

    # 七、 入党介绍人
    intro1_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="介绍人1姓名")
    intro1_post = models.CharField(max_length=50, null=True, blank=True, verbose_name="介绍人1职务")
    intro1_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="介绍人1电话")
    intro2_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="介绍人2姓名")
    intro2_post = models.CharField(max_length=50, null=True, blank=True, verbose_name="介绍人2职务")
    intro2_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="介绍人2电话")

    # 八、 预备党员的教育考察和转正
    regular_apply_time = models.DateField(null=True, blank=True, verbose_name="转正申请时间")
    regular_mass_meeting_time = models.DateField(null=True, blank=True, verbose_name="转正征求群众意见时间")
    regular_public_time = models.DateField(null=True, blank=True, verbose_name="转正公示时间")
    regular_public_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name="公示情况")
    regular_meeting_time = models.DateField(null=True, blank=True, verbose_name="支部大会讨论时间")
    regular_vote_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name="表决情况")
    regular_approve_opinion = models.CharField(max_length=255, null=True, blank=True, verbose_name="上级党委审批意见")
    regular_approve_time = models.DateField(null=True, blank=True, verbose_name="审批时间")

    class Meta:
        verbose_name = "党员发展纪实档案"
        verbose_name_plural = verbose_name

# 自动创建档案信号：当 UserProfile 被创建时，自动为其生成一张空白的电子档案
@receiver(post_save, sender=UserProfile)
def create_member_record(sender, instance, created, **kwargs):
    if created:
        PartyMemberRecord.objects.create(user=instance)