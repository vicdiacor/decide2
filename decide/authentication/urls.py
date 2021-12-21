from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from .views import GetUserView, LogoutView, RegisterView, UserVotings, exportGroup, importGroup


urlpatterns = [
    path('login/', obtain_auth_token),
    path('logout/', LogoutView.as_view()),
    path('getuser/', GetUserView.as_view()),
    path('register/', RegisterView.as_view()),
    path('userVotings/<int:voterId>', UserVotings),
    path('groups/import/', importGroup),
    path('groups/export/', exportGroup)
]
    