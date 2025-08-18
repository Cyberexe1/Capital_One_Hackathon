from django.urls import path
from .views import (
    price_prediction_view,
    price_all_view,
    advisory_view,
    text_to_speech_view,
    process_speech_view,
)

urlpatterns = [
    path("price/", price_prediction_view, name="price_prediction"),
    path("price/all/", price_all_view, name="price_all"),
    path("advisory/", advisory_view, name="advisory"),
    path("text-to-speech/", text_to_speech_view, name="text_to_speech"),
    path("process-speech/", process_speech_view, name="process_speech"),
]
