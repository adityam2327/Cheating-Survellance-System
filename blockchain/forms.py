from django import forms

class BlockchainEventForm(forms.Form):
    event_type = forms.CharField(max_length=100)
    severity = forms.CharField(max_length=50)
    description = forms.CharField(widget=forms.Textarea)
    confidence_score = forms.FloatField(required=False)
    screenshot_path = forms.CharField(max_length=255, required=False)
    metadata = forms.CharField(widget=forms.Textarea, required=False)
    session_id = forms.CharField(max_length=100, required=False)
    user_id = forms.CharField(max_length=100, required=False) 