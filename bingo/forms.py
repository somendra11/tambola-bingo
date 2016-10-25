from django import forms

class CreateGameForm(forms.Form):
    start_time = forms.CharField(max_length=40, required=True)
    finishing_time = forms.CharField(max_length=40, required=True)
    announcement_duration = forms.IntegerField(required=True)