from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED,
        HTTP_400_BAD_REQUEST,
        HTTP_401_UNAUTHORIZED
)
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ObjectDoesNotExist

from .serializers import UserSerializer

from authentication.forms import *
from authentication.import_and_export import * 
from django.contrib import messages


class GetUserView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        tk = get_object_or_404(Token, key=key)
        return Response(UserSerializer(tk.user, many=False).data)


class LogoutView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        try:
            tk = Token.objects.get(key=key)
            tk.delete()
        except ObjectDoesNotExist:
            pass

        return Response({})


class RegisterView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        tk = get_object_or_404(Token, key=key)
        if not tk.user.is_superuser:
            return Response({}, status=HTTP_401_UNAUTHORIZED)

        username = request.data.get('username', '')
        pwd = request.data.get('password', '')
        if not username or not pwd:
            return Response({}, status=HTTP_400_BAD_REQUEST)

        try:
            user = User(username=username)
            user.set_password(pwd)
            user.save()
            token, _ = Token.objects.get_or_create(user=user)
        except IntegrityError:
            return Response({}, status=HTTP_400_BAD_REQUEST)
        return Response({'user_pk': user.pk, 'token': token.key}, HTTP_201_CREATED)



### Importar/Exportar

def importGroup(request):
    form = importForm()

    if request.method == 'POST':
        form = importForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name'] 
            file = request.FILES['file']

            # Por cada usuario del fichero, indicado por nombre de usuario
                # Recuperar el usuario, comprobar que existe, añadir a una lista
            users_list = readTxtFile(file)

            # Si todos los usuarios existen, creo el grupo y añado todos los usuarios de la lista
            if (users_list != None):
                b = createGroup(name, users_list)
                # Si b==False, entonces ya existía un grupo con mismo nombre
                if (b):
                    messages.success(request, "Grupo creado correctamente.")
                else:
                    messages.error(request, "Ya existe un grupo con el mismo nombre.")
            else:
                messages.error(request, "Uno de los usuarios indicados no existe.")


    return render(request, 'import_group.html', {'form': form})
        
        