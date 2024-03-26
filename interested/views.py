from django.shortcuts import render


def interested_index(request):
    return render(
        request,
        "interested/interested_index.html",
    )


def interested_offers(request):
    return render(request, "interested/interested_offers.html")


def interested_philosophy(request):
    return render(request, "interested/interested_philosophy.html", {})
