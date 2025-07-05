from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Violation

@login_required
def violation_list(request):
    violations = Violation.objects.filter(user=request.user)
    return render(request, 'violations/violation_list.html', {'violations': violations})

@login_required
def violation_detail(request, violation_id):
    violation = get_object_or_404(Violation, id=violation_id, user=request.user)
    return render(request, 'violations/violation_detail.html', {'violation': violation}) 