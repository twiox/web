from django.shortcuts import render, redirect
from interested.models import PublicEvent


def landingPage(request):
    public_events = [x for x in PublicEvent.objects.all() if not x.is_past_due]
    return render(
        request, "main/landing.html", context={"public_events": public_events}
    )


def impressumPage(request):
    return render(request, "main/impressum.html", context={})


def dataProtectionPage(request):
    return render(request, "main/dataprotection.html", context={})
