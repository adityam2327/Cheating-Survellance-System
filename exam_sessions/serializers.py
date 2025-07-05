from rest_framework import serializers
from .models import ExamSession, SessionEvent

class SessionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionEvent
        fields = '__all__'

class SessionSerializer(serializers.ModelSerializer):
    events = SessionEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = ExamSession
        fields = '__all__'
        read_only_fields = ('user', 'session_id', 'start_time') 