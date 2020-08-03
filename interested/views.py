from django.shortcuts import render
from django.contrib import messages
from .forms import ProbetrainingForm

def interested_index(request):
    if (request.method == "POST"):
        form = ProbetrainingForm(request.POST) #if no files
        if form.is_valid():
            messages.add_message(request, messages.SUCCESS, 'Anmeldung verschickt')
            #Todo: Send Email to both 
        else:
            return render(request,"interested/interested_index.html",{"form":form})
    form = ProbetrainingForm()
    return render(request,"interested/interested_index.html",{"form":form})
