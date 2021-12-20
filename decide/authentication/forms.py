from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField(max_length=254)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )

class importForm(forms.Form):
    name = forms.CharField(max_length=80, min_length=1, label='Nombre del grupo', required=True)
    file = forms.FileField(label='Archivo txt o xlsx', required=True)


class exportForm(forms.Form):
    group = forms.ModelChoiceField(label='Selecciona grupo a exportar', queryset=Group.objects.all())
    
