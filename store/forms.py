from django import forms


class ReviewForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label='')

class SearchForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label='')
