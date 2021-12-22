from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from authentication.views import *


from .views import GetUserView, LogoutView, RegisterView, UserVotings, exportGroup, importGroup


urlpatterns = [

    path('registrarse/', registro),
    path('cerrar_sesion/', cerrar_sesion),
    path('iniciar_sesion/', iniciar_sesion),
    path('login/', obtain_auth_token),
    path('logout/', LogoutView.as_view()),
    path('getuser/', GetUserView.as_view()),
    path('register/', RegisterView.as_view()),
    path('userVotings/<int:voterId>', UserVotings),
    path('groups/import/', importGroup),
    path('groups/export/', exportGroup),
    path('notifications_admin/', voting_admin_notification),
    path('notifications/', voting_user_notification),
]
    