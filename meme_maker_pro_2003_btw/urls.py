from django.urls import path

from meme_maker_pro_2003_btw.views import IndexView, MemeView, StreamView

urlpatterns = [
    path("", IndexView.as_view()),
    path("meme", MemeView.as_view()),
    path("sse", StreamView.as_view()),
]
