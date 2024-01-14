from django.shortcuts import render


def landing(request):
    return render(request, "main/main.html", {})


def impressum(request):
    return render(request, "main/impressum.html", {})


def dataprotection(request):
    return render(request, "main/dataprotection.html", {})
