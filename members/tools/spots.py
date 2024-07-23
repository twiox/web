from django.views.generic import ListView, UpdateView, CreateView
from django.urls import path
from members.models import Spot
from members.forms import SpotForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse


def get_location_date(request):
    locations = []
    for spot in Spot.objects.all():
        locations.append(spot.get_location_features())
    return JsonResponse(locations, safe=False)


class SpotListView(ListView):
    model = Spot
    template_name = "pages/spot_list.html"


class SpotCreateView(CreateView):
    model = Spot
    form_class = SpotForm
    template_name = "pages/spot_form.html"


class SpotUpdateView(UpdateView):
    model = Spot
    form_class = SpotForm
    template_name = "pages/spot_form.html"


urlpatterns = [
    path("list/", SpotListView.as_view(), name="spot_list"),
    path("neu/", SpotCreateView.as_view(), name="spot_create"),
    path("<int:pk>/ändern/", SpotUpdateView.as_view(), name="spot_update"),
    path("geojson", get_location_date, name="get_location_data"),
]
