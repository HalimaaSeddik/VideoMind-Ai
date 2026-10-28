from django.urls import path

from . import views


urlpatterns = [
    path("health/", views.health_check, name="health-check"),
    path(
        "videos/process/",
        views.process_video_view,
        name="process-video",
    ),
    path(
        "videos/<str:video_id>/ask/",
        views.ask_question_view,
        name="ask-question",
    ),
]