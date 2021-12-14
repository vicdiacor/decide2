from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from authentication.views import registro, cerrar_sesion, iniciar_sesion

urlpatterns = [

    path('register/', registro),
    path('cerrar_sesion/', cerrar_sesion),
    path('iniciar_sesion/', iniciar_sesion)
]