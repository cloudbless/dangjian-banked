# backend/learning/serializers.py
from rest_framework import serializers
from .models import Course, StudyRecord, Question, Option # 👇 引入新模型

from .models import Course, StudyRecord, Question, Option # 👇 引入新模型
class CourseSerializer(serializers.ModelSerializer):
    publisher_name = serializers.CharField(source='publisher.username', read_only=True)
    
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['publisher', 'organization', 'created_at']

class StudyRecordSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = StudyRecord
        fields = '__all__'
        read_only_fields = ['user', 'is_completed']
# 👇 新增：选项序列化器
class OptionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) # 允许不传ID（用于新建）
    
    class Meta:
        model = Option
        fields = ['id', 'content', 'is_correct']

# 👇 新增：题目序列化器（包含嵌套的选项）
class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'course', 'content', 'q_type', 'analysis', 'options']

    def create(self, validated_data):
        options_data = validated_data.pop('options')
        question = Question.objects.create(**validated_data)
        # 批量创建选项
        for option_data in options_data:
            Option.objects.create(question=question, **option_data)
        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        instance.content = validated_data.get('content', instance.content)
        instance.q_type = validated_data.get('q_type', instance.q_type)
        instance.analysis = validated_data.get('analysis', instance.analysis)
        instance.save()

        if options_data is not None:
            # 简单策略：全删全建更新选项
            instance.options.all().delete()
            for option_data in options_data:
                Option.objects.create(question=instance, **option_data)
        return instance