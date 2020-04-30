from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import MemberCreationForm, ProfileCreationForm, TrainerCreationForm
from members.models import Group

from django.contrib.auth.decorators import permission_required, login_required

#register user
@login_required
@permission_required('auth.add_user', raise_exception=True)
def register(request):
    if(request.method == "POST"): #if the form is filled out
        form = MemberCreationForm(request.POST) 
        form2 = ProfileCreationForm(request.POST)
        
        if(form.is_valid() and form2.is_valid()): #and the form is valid (= submitted and passwords match etc.)
            real_user = form.save() #save the user to fire the signal
            real_user.refresh_from_db() #get the user again
            real_user.profile.group = form2.cleaned_data.get('group') #add the user's group
            real_user.profile.member_num = form2.cleaned_data.get('member_num') #add the user's number
            real_user.save() #save the entries
            messages.success(request, "Account created")
            return redirect("register")
    else:
        form = MemberCreationForm()
        form2 = ProfileCreationForm()
    return render(request, 'user_handling/register.html', context={"form":form, "form2":form2})

@login_required
@permission_required('members.add_trainer', raise_exception=True)
def register_trainer(request):
    if(request.method == "POST"): #if the form is filled out
        form = TrainerCreationForm(request.POST) 
        if(form.is_valid()): #and the form is valid (= submitted and passwords match etc.)
            new_trainer = form.save() #save the trainer

            messages.success(request, "Trainer created")
            return redirect("register_trainer")
    else:
        form = TrainerCreationForm()
    return render(request, 'user_handling/register_trainer.html', context={"form":form})
    
    
    
    
    
    
    
    
    
    
    
    
    
    