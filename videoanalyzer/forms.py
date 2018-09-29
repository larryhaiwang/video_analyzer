from django import forms
from django.contrib.auth.models import User
# ugettext_lazy() is Django's translation function. It is a good practice if you want to translate your site later.
from django.utils.translation import ugettext_lazy as _

'''
define a form for user registration based on django's UserCreationForm
    # fields -
        * username, password1, password2: standard fields in UserCreationForm    
        * first_name, last_name: name of the new user
        * email: email of the new user
'''
from django.contrib.auth.forms import UserCreationForm

class UserRegistrationForm(UserCreationForm):
    # define addtional fields besides UserCreationForm
    first_name = forms.CharField(max_length=50, label='First Name')
    last_name = forms.CharField(max_length=50, label='Last Name')
    email = forms.EmailField(label='Email', help_text=_('Enter your email for password reset.'))
    
    class Meta:
        model = User
        fields = ['username','first_name','last_name','email','password1','password2']
    # override save function to save all fields above to User model
    def save(self, commit=True):
        # retrieve the user from UseCreationForm. username, password1 and password2 have already been stored in the user
        user = super(UserRegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        # save record in User model if commit is true
        if commit:
            user.save()
        return user