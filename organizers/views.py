from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from members.models import Chairman
from .forms import OrganizerForm
  
def organizers_index(request):
    chairmen = Chairman.objects.filter(show__contains="event_site")
    if (request.method == "POST"):
        form = OrganizerForm(request.POST) #if no files
        if form.is_valid():
            #get Form data
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            int_email = form.cleaned_data.get('email')
            telnr = form.cleaned_data.get('telephone')
            notes = form.cleaned_data.get('notes')
            
            mail_subject=f"Anfrage Veranstalter {first_name} {last_name}"
            message=render_to_string("organizers/organizers_email.html",{
                "first_name":first_name,
                "last_name":last_name,
                "email": int_email,
                "telnr": telnr,
                "notes":notes,
                }       
            )
            email=EmailMessage(mail_subject, message, to=[settings.TO_EMAIL])
            email.send()
            #And the message to the interested
            message2 =render_to_string("organizers/organizers_email_answer.html",{
                "first_name":first_name,
                "last_name":last_name
                }       
            )
            EmailMessage(f"Twio X e.V. - Deine Anfrage", message2, to=[int_email]).send()
            messages.add_message(request, messages.SUCCESS, 'Anfrage erfolgreich verschickt')
            return HttpResponseRedirect("")
        else:
            return render(request,"organizers/organizers_index.html",{"form":form, "chairmen":chairmen})
    form = OrganizerForm() 
    return render(request, "organizers/organizers_index.html", {"form":form,"chairmen":chairmen})

