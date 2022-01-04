from django.urls import path
from .views import BoothView, ChildBoothView


urlpatterns = [
    path('<int:voting_id>/', BoothView.as_view()),
    path('<int:voting_id>/<int:child_id>/', ChildBoothView.as_view()),
]
