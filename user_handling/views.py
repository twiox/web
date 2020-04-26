from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import MemberCreationForm, ProfileCreationForm, TrainerCreationForm, GroupForm
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

@login_required
#@permission_required('auth.add_user', raise_exception=True)

def register_trainer(request):
    if(request.method == "POST"): #if the form is filled out
        form = TrainerCreationForm(request.POST) 
        form2 = GroupForm(request.POST)
        if(form.is_valid() and form2.is_valid()): #and the form is valid (= submitted and passwords match etc.)
            new_trainer = form.save() #save the trainer
            all_groups = form2.cleaned_data["groups"] #get the choosen groups
            
            for group in all_groups:
                group.trainer.add(new_trainer) 
                group.save()
            
            messages.success(request, "Trainer created")
            return redirect("register_trainer")
    else:
        form = TrainerCreationForm()
        form2 = GroupForm()
    return render(request, 'user_handling/register_trainer.html', context={"form":form,"form2":form2})
    
    
    
    
    
    
    
    
    
    
    
    
    
    