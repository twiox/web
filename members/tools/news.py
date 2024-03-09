from members.models import News
from django.shortcuts import render
from django.urls import path


def get_section(request):
    posts = News.objects.all().order_by("-id")

    context = {
        "posts": posts,
    }

    return render(request, "sections/news_section.html", context)


urlpatterns = [
    path("get-section", get_section, name="get_news_section"),
]
