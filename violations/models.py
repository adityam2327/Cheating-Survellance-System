from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Violation(models.Model):
    VIOLATION_TYPES = [
        ('head_misalignment', 'Head Misalignment'),
        ('eye_misalignment', 'Eye Misalignment'),
        ('mobile_detection', 'Mobile Detection'),
        ('lip_movement', 'Lip Movement'),
        ('emotion_detection', 'Emotion Detection'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    violation_type = models.CharField(max_length=30, choices=VIOLATION_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    confidence = models.FloatField(default=0.0)
    description = models.TextField(blank=True)
    screenshot_path = models.CharField(max_length=500, blank=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.violation_type} - {self.user.username} - {self.timestamp}" 