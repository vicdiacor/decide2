from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED,
        HTTP_400_BAD_REQUEST,
        HTTP_401_UNAUTHORIZED
)

from rest_framework.views import APIView
from rest_framework import generics, permissions
from django.views.generic import TemplateView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ObjectDoesNotExist

from .serializers import UserSerializer
from census.models import Census
from voting.models import Voting

from authentication.forms import *
from authentication.import_and_export import * 
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import datetime


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


FILE_PATH = 'authentication/files/'
FORMATS = {'excel':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'txt': 'text/plain'}


def importGroup(request):
    form = importForm()

    if request.method == 'POST':
        form = importForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name'] 
            file = request.FILES['file']
            format = file.content_type

            users_list = []
            # Si file es excel, guardo el archivo para abrirlo después
            if (format == FORMATS['excel']):
                path = default_storage.save(FILE_PATH + 'temp_import.xlsx', ContentFile(file.read()))
                users_list = readExcelFile(path)
                os.remove(os.path.join(path))   # Borro el archivo tras su uso
            # Si file es txt, no necesito guardar el fichero
            elif (format == FORMATS['txt']):
                users_list = readTxtFile(file)
            else:
                messages.error(request, "Formato de archivo no válido.")
                return render(request, 'import_group.html', {'form': form})

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
        


def exportGroup(request):
    form = exportForm()

    if request.method == 'POST':
        form = exportForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.cleaned_data['group']
            users = User.objects.filter(groups=group)
            
            # Crea el Excel con los usuarios exportados
            writeInExcelUsernames(users, FILE_PATH + 'temp_export.xlsx', 'temp_export.xlsx')
                
            # Abrir el Excel generado
            with open(FILE_PATH + 'temp_export.xlsx', 'rb') as excel:
                data = excel.read()

            # Automáticamente descarga el archivo
            resp = HttpResponse(data, content_type=FORMATS['excel'])
            resp['Content-Disposition'] = 'attachment; filename=export_group.xlsx'
            return resp

    return render(request, 'export_group.html', {'form': form})


def UserVotings(request,voterId):
    voter = User.objects.get(id=voterId)
    cens = Census.objects.filter(voter_id=voterId).values_list('voting_id',flat=True)
    votAbiertas = []
    votCerradas = []
    votPendientes = []
    for i in cens:
        votacion = Voting.objects.get(id=i)
        if (votacion.start_date==None):
            votPendientes.append(i)
        elif(votacion.end_date==None):
            votAbiertas.append(i)
        else:
            votCerradas.append(i)
    context = {'voter': voter,'total':cens, 'abiertas':votAbiertas, 'cerradas':votCerradas,'pendientes':votPendientes}        
    return render(request,'view_voting.html',context)