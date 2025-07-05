from django.contrib import admin
from .models import Violation

@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ('user', 'violation_type', 'timestamp', 'confidence', 'is_resolved')
    list_filter = ('violation_type', 'is_resolved', 'timestamp')
    search_fields = ('user__username', 'description') 