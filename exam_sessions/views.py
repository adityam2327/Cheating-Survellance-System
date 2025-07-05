from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import ExamSession, SessionEvent
from .serializers import SessionSerializer, SessionEventSerializer
import uuid

@login_required
def session_list(request):
    """Display list of user's exam sessions"""
    sessions = ExamSession.objects.filter(user=request.user)
    return render(request, 'exam_sessions/session_list.html', {'sessions': sessions})

@login_required
def session_detail(request, session_id):
    """Display detailed view of a specific session"""
    session = get_object_or_404(ExamSession, id=session_id, user=request.user)
    events = SessionEvent.objects.filter(session=session)
    return render(request, 'exam_sessions/session_detail.html', {
        'session': session,
        'events': events
    })

@login_required
def create_session(request):
    """Create a new exam session"""
    if request.method == 'POST':
        session_id = str(uuid.uuid4())
        session = ExamSession.objects.create(
            user=request.user,
            session_id=session_id,
            exam_title=request.POST.get('exam_title', 'Online Exam'),
            duration_minutes=int(request.POST.get('duration_minutes', 120))
        )
        messages.success(request, f'Session {session_id} created successfully!')
        return redirect('exam_sessions:session_detail', session_id=session.id)
    
    return render(request, 'exam_sessions/create_session.html')

@login_required
def end_session(request, session_id):
    """End an active exam session"""
    session = get_object_or_404(ExamSession, id=session_id, user=request.user)
    if session.is_active:
        session.is_active = False
        session.save()
        messages.success(request, 'Session ended successfully!')
    return redirect('exam_sessions:session_list')

# API Views
class SessionListAPIView(generics.ListCreateAPIView):
    queryset = ExamSession.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]

class SessionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExamSession.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated] 