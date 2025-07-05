import time
import uuid
from typing import Dict, Any, Optional
from blockchain_logger import CheatingEvent, initialize_blockchain_logger, get_blockchain_logger

class BlockchainIntegration:
    """Integration layer for blockchain logging in the cheating surveillance system"""
    
    def __init__(self):
        """Initialize blockchain integration"""
        self.logger = initialize_blockchain_logger()
        self.session_id = str(uuid.uuid4())
        print(f"Blockchain integration initialized with session ID: {self.session_id}")
    
    def log_head_misalignment(self, direction: str, confidence: float, 
                             screenshot_path: Optional[str] = None, 
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log head misalignment event"""
        severity = self._determine_severity(confidence)
        description = f"Head misalignment detected: {direction}"
        
        event = CheatingEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type="head_misalignment",
            severity=severity,
            description=description,
            confidence_score=confidence,
            screenshot_path=screenshot_path,
            metadata=metadata or {},
            session_id=self.session_id
        )
        
        return self.logger.log_event(event)
    
    def log_eye_misalignment(self, direction: str, confidence: float,
                            screenshot_path: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log eye misalignment event"""
        severity = self._determine_severity(confidence)
        description = f"Eye misalignment detected: {direction}"
        
        event = CheatingEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type="eye_misalignment",
            severity=severity,
            description=description,
            confidence_score=confidence,
            screenshot_path=screenshot_path,
            metadata=metadata or {},
            session_id=self.session_id
        )
        
        return self.logger.log_event(event)
    
    def log_mobile_detection(self, confidence: float,
                           screenshot_path: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log mobile device detection event"""
        severity = self._determine_severity(confidence)
        description = "Mobile device detected during exam"
        
        event = CheatingEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type="mobile_detection",
            severity=severity,
            description=description,
            confidence_score=confidence,
            screenshot_path=screenshot_path,
            metadata=metadata or {},
            session_id=self.session_id
        )
        
        return self.logger.log_event(event)
    
    def log_lip_movement(self, lip_state: str, is_whispering: bool, confidence: float,
                        screenshot_path: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log lip movement/whispering event"""
        severity = "high" if is_whispering else "medium"
        description = f"Lip movement detected: {lip_state}" + (" (Whispering)" if is_whispering else "")
        
        event = CheatingEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type="lip_movement",
            severity=severity,
            description=description,
            confidence_score=confidence,
            screenshot_path=screenshot_path,
            metadata=metadata or {},
            session_id=self.session_id
        )
        
        return self.logger.log_event(event)
    
    def log_emotion_detection(self, emotion: str, stress_detected: bool, 
                            fear_detected: bool, overconfidence_detected: bool,
                            confidence: float, screenshot_path: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log emotion detection event"""
        # Determine severity based on detected emotions
        if stress_detected or fear_detected or overconfidence_detected:
            severity = "high"
            concerning_emotions = []
            if stress_detected:
                concerning_emotions.append("stress")
            if fear_detected:
                concerning_emotions.append("fear")
            if overconfidence_detected:
                concerning_emotions.append("overconfidence")
            description = f"Concerning emotions detected: {', '.join(concerning_emotions)}"
        else:
            severity = "low"
            description = f"Emotion detected: {emotion}"
        
        event = CheatingEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type="emotion_detection",
            severity=severity,
            description=description,
            confidence_score=confidence,
            screenshot_path=screenshot_path,
            metadata=metadata or {},
            session_id=self.session_id
        )
        
        return self.logger.log_event(event)
    
    def log_custom_event(self, event_type: str, description: str, severity: str,
                        confidence: float, screenshot_path: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log a custom cheating detection event"""
        event = CheatingEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type=event_type,
            severity=severity,
            description=description,
            confidence_score=confidence,
            screenshot_path=screenshot_path,
            metadata=metadata or {},
            session_id=self.session_id
        )
        
        return self.logger.log_event(event)
    
    def _determine_severity(self, confidence: float) -> str:
        """Determine severity based on confidence score"""
        if confidence >= 0.9:
            return "critical"
        elif confidence >= 0.7:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics for current session"""
        try:
            stats = self.logger.get_statistics()
            # Filter for current session
            session_events = self.logger.get_events_by_type("all", limit=1000)  # Get all events
            session_events = [e for e in session_events if e.session_id == self.session_id]
            
            session_stats = {
                'session_id': self.session_id,
                'total_session_events': len(session_events),
                'events_by_type': {},
                'events_by_severity': {},
                'session_start_time': min([e.timestamp for e in session_events]) if session_events else None,
                'session_end_time': max([e.timestamp for e in session_events]) if session_events else None
            }
            
            # Count events by type and severity for this session
            for event in session_events:
                session_stats['events_by_type'][event.event_type] = \
                    session_stats['events_by_type'].get(event.event_type, 0) + 1
                session_stats['events_by_severity'][event.severity] = \
                    session_stats['events_by_severity'].get(event.severity, 0) + 1
            
            return session_stats
            
        except Exception as e:
            print(f"Error getting session statistics: {e}")
            return {}
    
    def export_session_logs(self, filepath: str) -> bool:
        """Export session logs to JSON file"""
        try:
            session_events = self.logger.get_events_by_type("all", limit=1000)
            session_events = [e for e in session_events if e.session_id == self.session_id]
            
            export_data = {
                'session_id': self.session_id,
                'export_timestamp': time.time(),
                'total_events': len(session_events),
                'events': []
            }
            
            for event in session_events:
                event_data = {
                    'event_id': event.event_id,
                    'timestamp': event.timestamp,
                    'event_type': event.event_type,
                    'severity': event.severity,
                    'description': event.description,
                    'confidence_score': event.confidence_score,
                    'screenshot_path': event.screenshot_path,
                    'metadata': event.metadata
                }
                export_data['events'].append(event_data)
            
            import json
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"Session logs exported to {filepath}")
            return True
            
        except Exception as e:
            print(f"Error exporting session logs: {e}")
            return False
    
    def flush_pending_events(self):
        """Force mining of pending events"""
        self.logger.flush_pending_events()
    
    def verify_chain_integrity(self) -> bool:
        """Verify blockchain integrity"""
        return self.logger.verify_chain()
    
    def cleanup_old_data(self, max_age_days: int = 30):
        """Clean up old screenshot files"""
        self.logger.cleanup_old_screenshots(max_age_days)

# Global blockchain integration instance
blockchain_integration = None

def initialize_blockchain_integration() -> BlockchainIntegration:
    """Initialize the global blockchain integration instance"""
    global blockchain_integration
    if blockchain_integration is None:
        blockchain_integration = BlockchainIntegration()
    return blockchain_integration

def get_blockchain_integration() -> BlockchainIntegration:
    """Get the global blockchain integration instance"""
    if blockchain_integration is None:
        raise RuntimeError("Blockchain integration not initialized. Call initialize_blockchain_integration() first.")
    return blockchain_integration

# Convenience functions for easy integration
def log_head_misalignment(direction: str, confidence: float, 
                         screenshot_path: Optional[str] = None, 
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Log head misalignment event (convenience function)"""
    integration = get_blockchain_integration()
    return integration.log_head_misalignment(direction, confidence, screenshot_path, metadata)

def log_eye_misalignment(direction: str, confidence: float,
                        screenshot_path: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Log eye misalignment event (convenience function)"""
    integration = get_blockchain_integration()
    return integration.log_eye_misalignment(direction, confidence, screenshot_path, metadata)

def log_mobile_detection(confidence: float,
                       screenshot_path: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Log mobile device detection event (convenience function)"""
    integration = get_blockchain_integration()
    return integration.log_mobile_detection(confidence, screenshot_path, metadata)

def log_lip_movement(lip_state: str, is_whispering: bool, confidence: float,
                    screenshot_path: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Log lip movement/whispering event (convenience function)"""
    integration = get_blockchain_integration()
    return integration.log_lip_movement(lip_state, is_whispering, confidence, screenshot_path, metadata)

def log_emotion_detection(emotion: str, stress_detected: bool, 
                        fear_detected: bool, overconfidence_detected: bool,
                        confidence: float, screenshot_path: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Log emotion detection event (convenience function)"""
    integration = get_blockchain_integration()
    return integration.log_emotion_detection(emotion, stress_detected, fear_detected, 
                                           overconfidence_detected, confidence, screenshot_path, metadata) 