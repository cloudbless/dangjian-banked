# backend/learning/models.py
from django.db import models
from system.models import UserProfile, Organization

class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="课程标题")
    description = models.TextField(blank=True, verbose_name="课程简介")
    # 视频链接（可以是上传到我们服务器的，也可以是外部链接，这里以直链为例）
    video_url = models.URLField(max_length=500, verbose_name="视频链接")
    # 或者用 FileField 上传视频: video_file = models.FileField(upload_to='videos/')
    
    cover = models.ImageField(upload_to='course_covers/', null=True, blank=True, verbose_name="课程封面")
    points_reward = models.IntegerField(default=10, verbose_name="奖励积分")
    
    # 发布人与可见范围
    publisher = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="发布人")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, verbose_name="所属组织(仅本组织可见)")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "课程管理"

    def __str__(self):
        return self.title


class StudyRecord(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="学习人")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="课程")
    
    # 学习进度与状态
    progress = models.IntegerField(default=0, verbose_name="已看时长(秒)")
    is_completed = models.BooleanField(default=False, verbose_name="是否完成")
    
    # 心得体会（党员看后提交的反馈）
    feedback = models.TextField(blank=True, verbose_name="心得体会")
    
    last_studied_at = models.DateTimeField(auto_now=True, verbose_name="最后学习时间")

    class Meta:
        # 同一个人同一门课只能有一条记录
        unique_together = ('user', 'course')
        verbose_name = "学习记录"

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"