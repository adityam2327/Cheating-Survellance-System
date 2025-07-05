from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ExamSession(models.Model):
    """Model to track exam sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, unique=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    exam_title = models.CharField(max_length=200, default="Online Exam")
    duration_minutes = models.IntegerField(default=120)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"Session {self.session_id} - {self.user.username}"

class SessionEvent(models.Model):
    """Model to track events during exam sessions"""
    EVENT_TYPES = [
        ('head_misalignment', 'Head Misalignment'),
        ('eye_misalignment', 'Eye Misalignment'),
        ('mobile_detection', 'Mobile Detection'),
        ('lip_movement', 'Lip Movement'),
        ('emotion_detection', 'Emotion Detection'),
        ('session_start', 'Session Start'),
        ('session_end', 'Session End'),
    ]
    
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    confidence = models.FloatField(default=0.0)
    metadata = models.JSONField(default=dict)
    screenshot_path = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.event_type} - {self.session.session_id}" 