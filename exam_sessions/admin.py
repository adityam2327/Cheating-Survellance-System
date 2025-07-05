from django.contrib import admin
from .models import ExamSession, SessionEvent

@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user', 'exam_title', 'start_time', 'is_active')
    list_filter = ('is_active', 'start_time')
    search_fields = ('session_id', 'user__username', 'exam_title')

@admin.register(SessionEvent)
class SessionEventAdmin(admin.ModelAdmin):
    list_display = ('session', 'event_type', 'timestamp', 'confidence')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('session__session_id', 'event_type') 