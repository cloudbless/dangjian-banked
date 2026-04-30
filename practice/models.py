# backend/practice/models.py
from django.db import models
from system.models import UserProfile, Organization

class PracticeActivity(models.Model):
    STATUS_CHOICES = ((0, '报名中'), (1, '进行中'), (2, '已结束'))

    title = models.CharField(max_length=200, verbose_name="活动主题")
    cover = models.ImageField(upload_to='practice_covers/', null=True, blank=True, verbose_name="封面")
    content = models.TextField(verbose_name="活动详情")
    location = models.CharField(max_length=200, verbose_name="活动地点")
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")
    capacity = models.IntegerField(default=50, verbose_name="招募人数")
    points_reward = models.IntegerField(default=5, verbose_name="积分奖励")
    status = models.IntegerField(choices=STATUS_CHOICES, default=0, verbose_name="状态")
    
    publisher = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="发布人")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, verbose_name="所属支部")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class ActivitySignUp(models.Model):
    # 👇 将状态拆分，3代表已发分（流程结束）
    SIGNUP_STATUS = ((0, '待审核'), (1, '已通过'), (2, '已驳回'), (3, '已发分'))

    activity = models.ForeignKey(PracticeActivity, on_delete=models.CASCADE, related_name='signups')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    status = models.IntegerField(choices=SIGNUP_STATUS, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('activity', 'user') # 每人只能报一次