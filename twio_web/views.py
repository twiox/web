from django.shortcuts import render, redirect

def landingPage(request):
    return render(request, "members/main/landing.html", context={})

def impressumPage(request):
    return render(request, "members/main/impressum.html", context={})

def dataProtectionPage(request):
    return render(request, "members/main/dataprotection.html", context={})