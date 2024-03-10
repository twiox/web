from django.urls import path
from members.models import Description, Event
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def get_description(request):
    # if the description exists already, just return the content
    if pk := request.GET.get("id", False):
        descr = Description.objects.get(pk=int(pk))
    else:
        # description doesnt exist yet
        event = Event.objects.get(pk=int(request.GET.get("event")))
        descr = Description(event=event)
        descr.save()
        descr.refresh_from_db()

    return JsonResponse(json.loads(descr.content) if descr.content else {"empty": True})


@csrf_exempt
def save_description(request):
    description = Description.objects.get(pk=int(request.GET.get("id")))
    data = json.loads(request.POST.get("data"))
    description.content = json.dumps(data)
    description.save()

    return JsonResponse({})


urlpatterns = [
    path("get", get_description, name="get-description"),
    path("save", save_description, name="save-description"),
]
