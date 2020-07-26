from django.shortcuts import render, redirect

def landingPage(request):
    return render(request, "members/landing.html", context={})