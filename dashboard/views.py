from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from exam_sessions.models import ExamSession, SessionEvent
from violations.models import Violation
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

@login_required
def dashboard_home(request):
    """Main dashboard view"""
    # Get user's active session
    active_session = ExamSession.objects.filter(user=request.user, is_active=True).first()
    
    # Get recent violations
    recent_violations = Violation.objects.filter(user=request.user).order_by('-timestamp')[:5]
    
    # Get session statistics
    total_sessions = ExamSession.objects.filter(user=request.user).count()
    completed_sessions = ExamSession.objects.filter(user=request.user, is_active=False).count()
    
    # Get today's events
    today = datetime.now().date()
    today_events = SessionEvent.objects.filter(
        session__user=request.user,
        timestamp__date=today
    ).count()
    
    context = {
        'active_session': active_session,
        'recent_violations': recent_violations,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'today_events': today_events,
    }
    
    return render(request, 'dashboard/index.html', context)

@login_required
def dashboard_data(request):
    """API endpoint for dashboard data"""
    # Get statistics for the last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Daily violation counts
    daily_violations = []
    for i in range(7):
        date = start_date + timedelta(days=i)
        count = Violation.objects.filter(
            user=request.user,
            timestamp__date=date
        ).count()
        daily_violations.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Violation types
    violation_types = {}
    violations = Violation.objects.filter(user=request.user)
    for violation in violations:
        v_type = violation.violation_type
        violation_types[v_type] = violation_types.get(v_type, 0) + 1
    
    return JsonResponse({
        'daily_violations': daily_violations,
        'violation_types': violation_types,
    })

@login_required
def real_time_stats(request):
    """Real-time statistics API endpoint"""
    try:
        # Get current session
        active_session = ExamSession.objects.filter(user=request.user, is_active=True).first()
        
        # Get recent violations (last 10 minutes)
        ten_minutes_ago = datetime.now() - timedelta(minutes=10)
        recent_violations = Violation.objects.filter(
            user=request.user,
            timestamp__gte=ten_minutes_ago
        ).order_by('-timestamp')[:10]
        
        # Get session events
        session_events = []
        if active_session:
            session_events = SessionEvent.objects.filter(
                session=active_session
            ).order_by('-timestamp')[:20]
        
        # Calculate real-time statistics
        total_violations_today = Violation.objects.filter(
            user=request.user,
            timestamp__date=datetime.now().date()
        ).count()
        
        violations_by_type = {}
        for violation in Violation.objects.filter(user=request.user, timestamp__date=datetime.now().date()):
            v_type = violation.violation_type
            violations_by_type[v_type] = violations_by_type.get(v_type, 0) + 1
        
        # Format violations for frontend
        formatted_violations = []
        for violation in recent_violations:
            formatted_violations.append({
                'id': violation.id,
                'type': violation.violation_type,
                'description': violation.description,
                'confidence': violation.confidence,
                'timestamp': violation.timestamp.strftime('%H:%M:%S'),
                'is_resolved': violation.is_resolved
            })
        
        # Format session events
        formatted_events = []
        for event in session_events:
            formatted_events.append({
                'id': event.id,
                'type': event.event_type,
                'confidence': event.confidence,
                'timestamp': event.timestamp.strftime('%H:%M:%S'),
                'metadata': event.metadata
            })
        
        return JsonResponse({
            'success': True,
            'active_session': {
                'id': active_session.id if active_session else None,
                'session_id': active_session.session_id if active_session else None,
                'start_time': active_session.start_time.strftime('%H:%M:%S') if active_session else None,
                'duration_minutes': int((datetime.now() - active_session.start_time).total_seconds() / 60) if active_session else 0
            },
            'recent_violations': formatted_violations,
            'session_events': formatted_events,
            'stats': {
                'total_violations_today': total_violations_today,
                'violations_by_type': violations_by_type,
                'session_duration_minutes': int((datetime.now() - active_session.start_time).total_seconds() / 60) if active_session else 0
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def start_monitoring(request):
    """Start the monitoring interface"""
    return render(request, 'dashboard/monitoring.html')

@login_required
def analytics_view(request):
    """Analytics dashboard"""
    return render(request, 'dashboard/analytics.html') 