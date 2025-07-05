from django.http import JsonResponse
from django.db.models import Count
from violations.models import Violation
from users.models import User
from django.utils import timezone
from datetime import timedelta

# Violations per type

def violations_per_type(request):
    data = (
        Violation.objects.values('violation_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return JsonResponse({'results': list(data)})

# Violations per user

def violations_per_user(request):
    data = (
        Violation.objects.values('user__username')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return JsonResponse({'results': list(data)})

# Violations over time (last 7 days)
def violations_over_time(request):
    today = timezone.now().date()
    results = []
    for i in range(7):
        day = today - timedelta(days=i)
        count = Violation.objects.filter(timestamp__date=day).count()
        results.append({'date': str(day), 'count': count})
    results.reverse()
    return JsonResponse({'results': results}) 