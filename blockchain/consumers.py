import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from blockchain_logger import get_blockchain_logger
from datetime import datetime, timedelta

class BlockchainConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("Blockchain WebSocket connection accepted.")
        
        # Add to blockchain group for broadcasting
        await self.channel_layer.group_add("blockchain_updates", self.channel_name)
        
        # Send initial blockchain stats
        await self.send_initial_stats()

    async def disconnect(self, close_code):
        # Remove from blockchain group
        await self.channel_layer.group_discard("blockchain_updates", self.channel_name)
        print(f"Blockchain WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data):
        """Handle incoming messages from the client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'stats_request')
            
            if message_type == 'stats_request':
                await self.send_blockchain_stats()
            elif message_type == 'events_request':
                limit = data.get('limit', 10)
                await self.send_recent_events(limit)
            elif message_type == 'block_request':
                block_index = data.get('block_index')
                if block_index is not None:
                    await self.send_block_details(block_index)
            elif message_type == 'subscribe_events':
                # Subscribe to real-time event updates
                await self.channel_layer.group_add("event_updates", self.channel_name)
            elif message_type == 'unsubscribe_events':
                # Unsubscribe from real-time event updates
                await self.channel_layer.group_discard("event_updates", self.channel_name)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing request: {str(e)}'
            }))

    async def send_initial_stats(self):
        """Send initial blockchain statistics"""
        stats = await self.get_blockchain_stats()
        await self.send(text_data=json.dumps({
            'type': 'initial_stats',
            'data': stats
        }))

    async def send_blockchain_stats(self):
        """Send current blockchain statistics"""
        stats = await self.get_blockchain_stats()
        await self.send(text_data=json.dumps({
            'type': 'blockchain_stats',
            'data': stats
        }))

    async def send_recent_events(self, limit=10):
        """Send recent blockchain events"""
        events = await self.get_recent_events(limit)
        await self.send(text_data=json.dumps({
            'type': 'recent_events',
            'data': events
        }))

    async def send_block_details(self, block_index):
        """Send details of a specific block"""
        block_data = await self.get_block_details(block_index)
        await self.send(text_data=json.dumps({
            'type': 'block_details',
            'data': block_data
        }))

    async def blockchain_event_update(self, event):
        """Handle blockchain event updates (called by group)"""
        await self.send(text_data=json.dumps({
            'type': 'event_update',
            'data': event['data']
        }))

    async def blockchain_block_mined(self, event):
        """Handle new block mined updates (called by group)"""
        await self.send(text_data=json.dumps({
            'type': 'block_mined',
            'data': event['data']
        }))

    @database_sync_to_async
    def get_blockchain_stats(self):
        """Get blockchain statistics"""
        try:
            logger = get_blockchain_logger()
            stats = logger.get_statistics()
            
            # Get additional stats
            chain_length = len(logger.chain)
            pending_events = len(logger.pending_events)
            
            # Get events by severity for last 7 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            all_events = logger.get_events_by_type('all', limit=1000)
            events_by_severity = {}
            events_by_type = {}
            
            for event in all_events:
                event_date = datetime.fromtimestamp(event.timestamp)
                if start_date <= event_date <= end_date:
                    events_by_severity[event.severity] = events_by_severity.get(event.severity, 0) + 1
                    events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1
            
            return {
                'total_blocks': stats.get('total_blocks', 0),
                'total_events': stats.get('total_events', 0),
                'average_mining_time': stats.get('average_mining_time', 0.0),
                'last_mining_time': stats.get('last_mining_time', 0.0),
                'chain_length': chain_length,
                'pending_events': pending_events,
                'events_by_severity': events_by_severity,
                'events_by_type': events_by_type,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'error': str(e),
                'total_blocks': 0,
                'total_events': 0,
                'chain_length': 0,
                'pending_events': 0
            }

    @database_sync_to_async
    def get_recent_events(self, limit=10):
        """Get recent blockchain events"""
        try:
            logger = get_blockchain_logger()
            events = logger.get_events_by_type('all', limit=limit)
            
            return [{
                'event_id': event.event_id,
                'timestamp': event.timestamp,
                'event_type': event.event_type,
                'severity': event.severity,
                'description': event.description,
                'confidence_score': event.confidence_score,
                'session_id': event.session_id,
                'user_id': event.user_id,
                'formatted_time': datetime.fromtimestamp(event.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            } for event in events]
        except Exception as e:
            return []

    @database_sync_to_async
    def get_block_details(self, block_index):
        """Get details of a specific block"""
        try:
            logger = get_blockchain_logger()
            if 0 <= block_index < len(logger.chain):
                block = logger.chain[block_index]
                return {
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'hash': block.calculate_hash(),
                    'previous_hash': block.previous_hash,
                    'merkle_root': block.merkle_root,
                    'nonce': block.nonce,
                    'events_count': len(block.events),
                    'events': [{
                        'event_id': event.event_id,
                        'event_type': event.event_type,
                        'severity': event.severity,
                        'description': event.description,
                        'timestamp': event.timestamp
                    } for event in block.events],
                    'formatted_time': datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                return {'error': 'Block index out of range'}
        except Exception as e:
            return {'error': str(e)}

# Utility function to broadcast blockchain updates
async def broadcast_blockchain_update(channel_layer, update_type, data):
    """Broadcast blockchain updates to all connected clients"""
    await channel_layer.group_send("blockchain_updates", {
        'type': f'blockchain_{update_type}',
        'data': data
    })

async def broadcast_event_update(channel_layer, event_data):
    """Broadcast new event to subscribed clients"""
    await channel_layer.group_send("event_updates", {
        'type': 'blockchain_event_update',
        'data': event_data
    })

async def broadcast_block_mined(channel_layer, block_data):
    """Broadcast new block mined to all clients"""
    await channel_layer.group_send("blockchain_updates", {
        'type': 'blockchain_block_mined',
        'data': block_data
    }) 