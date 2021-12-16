import logging as log
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED as ST_201,
    HTTP_204_NO_CONTENT as ST_204,
    HTTP_400_BAD_REQUEST as ST_400,
    HTTP_401_UNAUTHORIZED as ST_401,
    HTTP_409_CONFLICT as ST_409
)

from base.perms import UserIsStaff
from .models import Census
from django.contrib.auth.models import Group

group_successfully_created = "Group successfully created"


class CensusCreate(generics.ListCreateAPIView):
    permission_classes = (UserIsStaff,)

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

    def check(self, user, group_name, groups):
        if not isinstance(group_name, str) or group_name.isspace():
            return Response('Group name is required', status=ST_400)
        group_name = group_name.strip()
        if Group.objects.filter(name=group_name).exists():
            return Response(f'Group with name \'{group_name}\' already exists, please, try another name', status=ST_409)
        if not groups or not isinstance(groups, list) or any(not isinstance(group, str) for group in groups) or len(groups) < 2:
            return Response('Two groups are required at least', status=ST_400)

        for group in groups:
            try:
                if user not in Group.objects.get(name=group).user_set.all():
                    return Response('User must be in all groups to perform this action', status=ST_401)
            except ObjectDoesNotExist:
                return Response(f'There is no group with name \'{group}\', please, try again', status=ST_400)

    class GroupUnion(generics.CreateAPIView):
        permissions_classes = (permissions.IsAuthenticated,)

        def create(self, request, *args, **kwargs):
            group_name = request.data.get('name')
            groups = request.data.get('groups')
            user = request.user

            checks = GroupOperations()
            response = checks.check(
                user=user, group_name=group_name, groups=groups)
            if response:
                return response

            new_group = Group.objects.create(name=group_name.strip())
            qs = Group.objects.get(name=groups[0]).user_set.all()
            for group in groups[1:]:
                qs = qs.union(Group.objects.get(
                    name=group).user_set.all())

            new_group.user_set.set(qs)
            return Response(group_successfully_created, status=ST_201)

    class GroupIntersection(generics.CreateAPIView):
        permissions_classes = (permissions.IsAuthenticated,)

        def create(self, request, *args, **kwargs):
            group_name = request.data.get('name')
            groups = request.data.get('groups')
            user = request.user

            checks = GroupOperations()
            response = checks.check(
                user=user, group_name=group_name, groups=groups)
            if response:
                return response

            new_group = Group.objects.create(name=group_name)
            qs = Group.objects.get(name=groups[0]).user_set.all()
            for group in groups[1:]:
                qs = qs.intersection(Group.objects.get(
                    name=group).user_set.all())

            new_group.user_set.set(qs)
            return Response(group_successfully_created, status=ST_201)

    class GroupDifference(generics.CreateAPIView):
        permissions_classes = (permissions.IsAuthenticated,)

        def create(self, request, *args, **kwargs):
            group_name = request.data.get('name')
            groups = request.data.get('groups')
            user = request.user

            checks = GroupOperations()
            response = checks.check(
                user=user, group_name=group_name, groups=groups)
            if response:
                return response

            new_group = Group.objects.create(name=group_name)
            qs = Group.objects.get(name=groups[0]).user_set.all()
            for group in groups[1:]:
                qs = qs.difference(Group.objects.get(
                    name=group).user_set.all())

            new_group.user_set.set(qs)
            return Response(group_successfully_created, status=ST_201)
