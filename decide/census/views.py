import logging as log
import json
from django.http import Http404
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.views.generic import TemplateView
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics, permissions
from rest_framework.response import Response
from .serializers import ParentGroupSerializer
from rest_framework.status import (
    HTTP_201_CREATED as ST_201,
    HTTP_204_NO_CONTENT as ST_204,
    HTTP_400_BAD_REQUEST as ST_400,
    HTTP_401_UNAUTHORIZED as ST_401,
    HTTP_409_CONFLICT as ST_409
)

from base.perms import UserIsStaff
from .models import Census, ParentGroup

group_successfully_created = "Group successfully created"


class CensusCreate(generics.ListCreateAPIView):
    permission_classes = (UserIsStaff,)
    
    
    def post(self, request):
            #Obtener grupo
            id_group= int(request.data.get('group_to_join'))
            id_user= int(request.data.get('userId'))
            try:
                group = ParentGroup.objects.get(id_group)
                user = User.objects.get(id_user)
                #Grupo publico
                if group !=None and user!= None:
                    if group.isPublic==True:
                        group.add(user)
                        group.save()
                #Grupo privado
                else:
                    return Response('No puedes unirte a un grupo privado', status=ST_409)
            except:
                return Response('Error try to add user to group', status=ST_409)
            return Response('User added to group', status=ST_201)
    

    def create(self, request, *args, **kwargs):
        voting_id = request.data.get('voting_id')
        voters = request.data.get('voters')
        try:
            for voter in voters:
                census = Census(voting_id=voting_id, voter_id=voter)
                census.save()
        except IntegrityError:
            return Response('Error try to create census', status=ST_409)
        return Response('Census created', status=ST_201)

    def list(self, request, *args, **kwargs):
        voting_id = request.GET.get('voting_id')
        voters = Census.objects.filter(
            voting_id=voting_id).values_list('voter_id', flat=True)
        return Response({'voters': voters})


class CensusDetail(generics.RetrieveDestroyAPIView):

    def destroy(self, request, voting_id, *args, **kwargs):
        voters = request.data.get('voters')
        census = Census.objects.filter(
            voting_id=voting_id, voter_id__in=voters)
        census.delete()
        return Response('Voters deleted from census', status=ST_204)

    def retrieve(self, request, voting_id, *args, **kwargs):
        voter = request.GET.get('voter_id')
        try:
            Census.objects.get(voting_id=voting_id, voter_id=voter)
        except ObjectDoesNotExist:
            return Response('Invalid voter', status=ST_401)
        return Response('Valid voter')


class GroupOperations():

    def check(self, user, group_name, groups, is_public):
        if not group_name or not isinstance(group_name, str) or group_name.isspace():
            return Response('Group name is required', status=ST_400)

        group_name = group_name.strip()
        if ParentGroup.objects.filter(name=group_name).exists():
            return Response(f'Group with name \'{group_name}\' already exists, please, try another name', status=ST_409)

        if not groups or not isinstance(groups, list) or any(not isinstance(group, str) for group in groups) or len(groups) < 2:
            return Response('Two groups are required at least', status=ST_400)

        if not isinstance(is_public, bool):
            return Response('If you wish the group to be private you must set \'is public\' attribute to false, otherwise set it to true', status=ST_400)

        for group in groups:
            try:
                if user not in ParentGroup.objects.get(name=group).user_set.all():
                    return Response('User must be in all groups to perform this action', status=ST_401)
            except ObjectDoesNotExist:
                return Response(f'There is no group with name \'{group}\', please, try again', status=ST_400)

    class GroupUnion(generics.CreateAPIView):
        permissions_classes = (permissions.IsAuthenticated,)

        def create(self, request, *args, **kwargs):
            group_name = request.data.get('name')
            groups = request.data.get('groups')
            is_public = request.data.get('is_public')
            log.info(
                f'{request.user} is trying to create group with name {group_name} and groups {groups} and is_public {is_public}')
            user = request.user

            checks = GroupOperations()
            response = checks.check(
                user=user, group_name=group_name, groups=groups, is_public=is_public)
            if response:
                return response

            new_group = ParentGroup.objects.create(
                name=group_name.strip(), isPublic=is_public)
            qs = ParentGroup.objects.get(name=groups[0]).user_set.all()
            for group in groups[1:]:
                qs = qs.union(ParentGroup.objects.get(
                    name=group).user_set.all())

            new_group.user_set.set(qs)
            return Response(group_successfully_created, status=ST_201)

    class GroupIntersection(generics.CreateAPIView):
        permissions_classes = (permissions.IsAuthenticated,)

        def create(self, request, *args, **kwargs):
            group_name = request.data.get('name')
            groups = request.data.get('groups')
            is_public = request.data.get('is_public')
            user = request.user

            checks = GroupOperations()
            response = checks.check(
                user=user, group_name=group_name, groups=groups, is_public=is_public)
            if response:
                return response

            new_group = ParentGroup.objects.create(
                name=group_name, isPublic=is_public)
            qs = ParentGroup.objects.get(name=groups[0]).user_set.all()
            for group in groups[1:]:
                qs = qs.intersection(ParentGroup.objects.get(
                    name=group).user_set.all())

            new_group.user_set.set(qs)
            return Response(group_successfully_created, status=ST_201)

    class GroupDifference(generics.CreateAPIView):
        permissions_classes = (permissions.IsAuthenticated,)

        def create(self, request, *args, **kwargs):
            group_name = request.data.get('name')
            groups = request.data.get('groups')
            is_public = request.data.get('is_public')
            user = request.user

            checks = GroupOperations()
            response = checks.check(
                user=user, group_name=group_name, groups=groups, is_public=is_public)
            if response:
                return response

            new_group = ParentGroup.objects.create(
                name=group_name, isPublic=is_public)
            qs = ParentGroup.objects.get(name=groups[0]).user_set.all()
            for group in groups[1:]:
                qs = qs.difference(ParentGroup.objects.get(
                    name=group).user_set.all())

            new_group.user_set.set(qs)
            return Response(group_successfully_created, status=ST_201)

# Listado de grupos públicos y privados


# TODO: check permissions and census
class GroupsView(TemplateView):
    template_name = 'groupList.html'
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        groups = ParentGroup.objects.all()

        diccionario= {}
        for group in groups:
            diccionario[group.pk]= {"name": group.name, "isPublic": group.isPublic }
       
        
        context['groups_info'] = diccionario
        print(json.dumps(diccionario))
        context['KEYBITS'] = settings.KEYBITS

        return context