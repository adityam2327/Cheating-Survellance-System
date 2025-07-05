from django.http import JsonResponse
from django.views import View
from blockchain_logger import get_blockchain_logger, CheatingEvent
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import BlockchainEventForm
import uuid
import time
import json
from datetime import datetime, timedelta

@method_decorator(login_required, name='dispatch')
class BlockchainLogsAPIView(View):
    def get(self, request):
        logger = get_blockchain_logger()
        # Get the most recent 100 events
        events = logger.get_events_by_type('all', limit=100)
        data = [
            {
                'event_id': e.event_id,
                'timestamp': e.timestamp,
                'event_type': e.event_type,
                'severity': e.severity,
                'description': e.description,
                'confidence_score': e.confidence_score,
                'screenshot_path': e.screenshot_path,
                'metadata': e.metadata,
                'session_id': e.session_id,
                'user_id': e.user_id,
            }
            for e in events
        ]
        return JsonResponse({'results': data})

@method_decorator(login_required, name='dispatch')
class BlockchainLogsView(View):
    def get(self, request):
        logger = get_blockchain_logger()
        events = logger.get_events_by_type('all', limit=100)
        return render(request, 'admin/blockchain_logs.html', {'blockchain_events': events})

@method_decorator(login_required, name='dispatch')
class BlockchainAddEventView(View):
    def get(self, request):
        form = BlockchainEventForm()
        return render(request, 'blockchain/add_event.html', {'form': form})

    def post(self, request):
        form = BlockchainEventForm(request.POST)
        if form.is_valid():
            logger = get_blockchain_logger()
            event = CheatingEvent(
                event_id=str(uuid.uuid4()),
                timestamp=time.time(),
                event_type=form.cleaned_data['event_type'],
                severity=form.cleaned_data['severity'],
                description=form.cleaned_data['description'],
                confidence_score=form.cleaned_data.get('confidence_score') or 0.0,
                screenshot_path=form.cleaned_data.get('screenshot_path'),
                metadata=json.loads(form.cleaned_data.get('metadata') or '{}'),
                session_id=form.cleaned_data.get('session_id'),
                user_id=form.cleaned_data.get('user_id'),
            )
            logger.log_event(event)
            return HttpResponseRedirect(reverse('blockchain:blockchain-dashboard'))
        return render(request, 'blockchain/add_event.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class BlockchainDashboardView(View):
    def get(self, request):
        logger = get_blockchain_logger()
        
        # Get blockchain statistics
        stats = logger.get_statistics()
        
        # Get recent events
        recent_events = logger.get_events_by_type('all', limit=10)
        
        # Get events by severity for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Get events by type
        events_by_type = {}
        events_by_severity = {}
        
        all_events = logger.get_events_by_type('all', limit=1000)
        for event in all_events:
            event_date = datetime.fromtimestamp(event.timestamp)
            if start_date <= event_date <= end_date:
                # Count by type
                events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1
                # Count by severity
                events_by_severity[event.severity] = events_by_severity.get(event.severity, 0) + 1
        
        # Get daily event counts for the last 7 days
        daily_events = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            count = sum(1 for event in all_events 
                       if datetime.fromtimestamp(event.timestamp).date() == date.date())
            daily_events.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        context = {
            'stats': stats,
            'recent_events': recent_events,
            'events_by_type': events_by_type,
            'events_by_severity': events_by_severity,
            'daily_events': daily_events,
            'chain_length': len(logger.chain),
            'pending_events': len(logger.pending_events),
        }
        
        return render(request, 'blockchain/dashboard.html', context)

@method_decorator(login_required, name='dispatch')
class BlockchainAPIView(View):
    def get(self, request):
        logger = get_blockchain_logger()
        
        # Get query parameters
        event_type = request.GET.get('event_type', 'all')
        severity = request.GET.get('severity', 'all')
        limit = int(request.GET.get('limit', 50))
        
        # Get events based on filters
        if event_type != 'all':
            events = logger.get_events_by_type(event_type, limit=limit)
        elif severity != 'all':
            events = logger.get_events_by_severity(severity, limit=limit)
        else:
            events = logger.get_events_by_type('all', limit=limit)
        
        data = [
            {
                'event_id': e.event_id,
                'timestamp': e.timestamp,
                'event_type': e.event_type,
                'severity': e.severity,
                'description': e.description,
                'confidence_score': e.confidence_score,
                'screenshot_path': e.screenshot_path,
                'metadata': e.metadata,
                'session_id': e.session_id,
                'user_id': e.user_id,
            }
            for e in events
        ]
        
        return JsonResponse({
            'results': data,
            'total_count': len(data),
            'filters': {
                'event_type': event_type,
                'severity': severity,
                'limit': limit
            }
        })

@method_decorator(login_required, name='dispatch')
class BlockExplorerView(View):
    def get(self, request):
        logger = get_blockchain_logger()
        
        # Get block index from URL parameter
        block_index = request.GET.get('block')
        
        if block_index:
            try:
                block_index = int(block_index)
                if 0 <= block_index < len(logger.chain):
                    block = logger.chain[block_index]
                    return render(request, 'blockchain/block_detail.html', {
                        'block': block,
                        'block_index': block_index
                    })
            except (ValueError, IndexError):
                pass
        
        # Show all blocks
        blocks = logger.chain
        return render(request, 'blockchain/block_explorer.html', {
            'blocks': blocks,
            'total_blocks': len(blocks)
        }) 