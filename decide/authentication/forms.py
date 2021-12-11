from django import forms
from django.contrib.auth.models import Group



class importForm(forms.Form):
    name = forms.CharField(max_length=80, min_length=1, label='Nombre del grupo', required=True)
    file = forms.FileField(label='Archivo txt', required=True)



class exportForm(forms.Form):
    group = forms.ModelChoiceField(label='Selecciona grupo a exportar', queryset=Group.objects.all())
    