# backend/learning/serializers.py
from rest_framework import serializers
from .models import Course, StudyRecord

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