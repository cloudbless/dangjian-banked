# backend/learning/models.py
from django.db import models
from system.models import UserProfile, Organization

class Course(models.Model):
    TYPE_CHOICES = (
        (1, '视频课程'),
        (2, '图文/练习题'),
    )
    title = models.CharField(max_length=200, verbose_name="课程标题")
    # 👇 新增：课程类型
    course_type = models.IntegerField(choices=TYPE_CHOICES, default=1, verbose_name="课程类型")
    description = models.TextField(blank=True, verbose_name="课程简介")
    
    # 👇 修改：视频链接改为非必填 (因为练习题可能没视频)
    video_url = models.URLField(max_length=500, null=True, blank=True, verbose_name="视频链接")
    # 👇 新增：用于存放练习题文本、题目或外部问卷链接的富文本
    content = models.TextField(blank=True, verbose_name="图文内容/练习题")
    
    cover = models.ImageField(upload_to='course_covers/', null=True, blank=True, verbose_name="课程封面")
    points_reward = models.IntegerField(default=10, verbose_name="奖励积分")
    
    publisher = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="发布人")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, verbose_name="所属组织")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "课程管理"

    def __str__(self):
        return self.title

# StudyRecord 保持不变...


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
# backend/learning/models.py (在文件末尾追加)

class Question(models.Model):
    TYPE_CHOICES = (
        ('single', '单选题'),
        ('multiple', '多选题'),
    )
    # 关联到课程，级联删除
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions', verbose_name="所属课程")
    content = models.TextField(verbose_name="题干")
    q_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='single', verbose_name="题目类型")
    analysis = models.TextField(blank=True, null=True, verbose_name="题目解析")

    class Meta:
        verbose_name = "习题"

    def __str__(self):
        return self.content[:20]

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    content = models.CharField(max_length=255, verbose_name="选项内容")
    is_correct = models.BooleanField(default=False, verbose_name="是否为正确答案")

    class Meta:
        verbose_name = "选项"

    def __str__(self):
        return self.content