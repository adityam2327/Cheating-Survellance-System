from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Violation
from blockchain_integration import get_blockchain_integration

@receiver(post_save, sender=Violation)
def log_violation_to_blockchain(sender, instance, created, **kwargs):
    if not created:
        return
    blockchain = get_blockchain_integration()
    violation_type = instance.violation_type
    # Map violation type to blockchain method
    if violation_type == 'head_misalignment':
        blockchain.log_head_misalignment(
            direction=instance.description or 'unknown',
            confidence=instance.confidence,
            screenshot_path=instance.screenshot_path,
            metadata={'user_id': instance.user.id}
        )
    elif violation_type == 'eye_misalignment':
        blockchain.log_eye_misalignment(
            direction=instance.description or 'unknown',
            confidence=instance.confidence,
            screenshot_path=instance.screenshot_path,
            metadata={'user_id': instance.user.id}
        )
    elif violation_type == 'mobile_detection':
        blockchain.log_mobile_detection(
            confidence=instance.confidence,
            screenshot_path=instance.screenshot_path,
            metadata={'user_id': instance.user.id}
        )
    elif violation_type == 'lip_movement':
        blockchain.log_lip_movement(
            lip_state=instance.description or 'unknown',
            is_whispering='whisper' in (instance.description or '').lower(),
            confidence=instance.confidence,
            screenshot_path=instance.screenshot_path,
            metadata={'user_id': instance.user.id}
        )
    elif violation_type == 'emotion_detection':
        # For demo, assume description contains emotion info
        blockchain.log_emotion_detection(
            emotion=instance.description or 'unknown',
            stress_detected='stress' in (instance.description or '').lower(),
            fear_detected='fear' in (instance.description or '').lower(),
            overconfidence_detected='overconfident' in (instance.description or '').lower(),
            confidence=instance.confidence,
            screenshot_path=instance.screenshot_path,
            metadata={'user_id': instance.user.id}
        )
    else:
        blockchain.log_custom_event(
            event_type=violation_type,
            description=instance.description or '',
            severity='medium',
            confidence=instance.confidence,
            screenshot_path=instance.screenshot_path,
            metadata={'user_id': instance.user.id}
        ) 