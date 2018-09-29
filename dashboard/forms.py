from django import forms
from django.utils.translation import ugettext_lazy as _

'''
define a form for user to upload a file
    # fields -
        * name: Files.name
        * file: Files.file
'''
from dashboard.models import Files

class FileUploadModelForm(forms.ModelForm):    
    class Meta:
        model = Files
        fields = ['name','file']