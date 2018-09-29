from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

'''
define a functional view that displays description of the site and login/register options. 
    # template - home.html
'''

def home_view(request):
    return render(request, 'home.html')

'''
define a functional view for user registration.
    # no email verification
    # form - UserRegistrationForm
    # template - user_signup.html
'''
from django.contrib.auth import login, authenticate
from videoanalyzer.forms import UserRegistrationForm

def user_registration_view(request):
    # check POST vs GET request
    if request.method == 'POST':
        # populate data from POST
        reg_form = UserRegistrationForm(request.POST)
        
        #create the user and login
        if reg_form.is_valid():
            # create the user
            reg_form.save()
            # login user
            username = reg_form.cleaned_data['username']
            password = reg_form.cleaned_data['password1']
            user = authenticate(username = username, password = password)
            login(request, user)
            # redirect to index page of dashboard app
            return HttpResponseRedirect(reverse('index'))
    # for GET request, display empty form
    else:
        reg_form = UserRegistrationForm()
    return render(request, 'user_signup.html', context={'form':reg_form})