from django.shortcuts import render
from members.models import Tester


def landing(request):
    # get new Tester requests
    new_tester = Tester.objects.filter(batch=None)
    return render(request, "main/layout.html", {"new_tester": new_tester})


def impressum(request):
    return render(request, "main/impressum.html", {})


def dataprotection(request):
    return render(request, "main/dataprotection.html", {})
