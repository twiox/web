from django.views.generic import ListView, UpdateView, CreateView
from django.urls import path
from members.models import Spot
from members.forms import SpotForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def get_location_date(request):
    locations = []
    for spot in Spot.objects.all():
        locations.append(spot.get_location_features())
    return JsonResponse(locations, safe=False)


class SpotListView(ListView):
    model = Spot
    template_name = "pages/spot_list.html"


@login_required
def main_spot_create(request):

    context = {"object": None, "type": "form", "form": SpotForm()}

    if request.method == "POST":
        form = SpotForm(request.POST)

        if form.is_valid():
            object = form.save()
            context.update(
                {
                    "object": object,
                    "type": "success",
                    "message": "Spot erfolgreich erstellt",
                }
            )

    return render(request, f"modals/spot_modal.html", context)


@login_required
def main_spot_update(request, pk):
    object = Spot.objects.get(pk=int(pk))

    form = SpotForm(request.POST, instance=object)
    form.save()

    context = {
        "object": object,
        "type": "success",
        "message": "Spot erfolgreich bearbeitet",
    }
    return render(request, f"modals/spot_modal.html", context)


@login_required
def main_spot_delete(request, pk):
    object = Spot.objects.get(pk=int(pk))
    message = "Spot erfolgreich gelöscht"
    try:
        object.delete()
    except:  # spot is still used by a session
        message = f"Spot in Benutzung, kann nicht gelöscht werden. Spots: {','.join([x.title for x in object.session.all()])}"

    context = {"object": object, "type": "success", "message": message}
    return render(request, f"modals/spot_modal.html", context)


urlpatterns = [
    path("list/", SpotListView.as_view(), name="spot_list"),
    path("neu/", main_spot_create, name="main_spot_create"),
    path("löschen/<int:pk>", main_spot_delete, name="main_spot_delete"),
    path("<int:pk>/ändern/", main_spot_update, name="main_spot_update"),
    path("geojson", get_location_date, name="get_location_data"),
]
