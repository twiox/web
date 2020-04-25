from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import MemberCreationForm, ProfileCreationForm
from members.models import Group


#register user
def register(request):
    if(request.method == "POST"): #if the form is filled out
        form = MemberCreationForm(request.POST) 
        form2 = ProfileCreationForm(request.POST)
        
        if(form.is_valid() and form2.is_valid()): #and the form is valid (= submitted and passwords match etc.)
            real_user = form.save(commit=False) #save the user in a variable
            profile = form2.save(commit=False) #save the profile in a variable
            #now set the user
            profile.user = real_user #add the user
            real_user.save() #save the entries
            profile.save()
            
            messages.success(request, "Account created")
            return redirect("register")
    else:
        form = MemberCreationForm()
        form2 = ProfileCreationForm(request.POST)
    return render(request, 'user_handling/register.html', context={"form":form, "form2":form2})
