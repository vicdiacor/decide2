from django import forms



class importForm(forms.Form):
    name = forms.CharField(max_length=80, min_length=1, label='Nombre del grupo', required=True)
    file = forms.FileField(label='Archivo txt', required=True)



#class exportarForm(forms.Form):
    