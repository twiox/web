from django.urls import path
from members.models import Description, Event, DescriptionImage
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


@csrf_exempt
def upload(request):
    """
    Upload entry point, should be called with 'file' or 'image' in request.FILES and
    'type' in request.GET
    """
    type = request.GET.get("type", None)

    # NO file, upload url
    if type == "url":
        url = json.loads(request.body).get("url")
        return JsonResponse(
            {
                "success": 1,
                "file": {
                    "url": url,
                },
            }
        )

    if type == "image":
        # now get the file
        image = request.FILES.get("image")
        img = DescriptionImage(image=image)
        img.save()
        img.refresh_from_db()

        if img.pk:
            success = 1
            url = img.image.url

        else:
            success = 0
            url = ""

        return JsonResponse(
            {
                "success": success,
                "file": {
                    "url": url,
                },
            }
        )


urlpatterns = [
    path("get", get_description, name="get-description"),
    path("save", save_description, name="save-description"),
    path("upload", upload, name="editor_upload"),
]
