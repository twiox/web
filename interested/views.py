from django.shortcuts import render

def interested_index(request):
    return render(request,"interested/interested_index.html",{})
