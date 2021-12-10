from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics
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

group_successfully_created = 'Group successfully created'


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


class GroupUnion(generics.CreateAPIView):
    permission_classes = (UserIsStaff,)

    def create(self, request, *args, **kwargs):
        group_name = request.data.get('group_name')
        group_ids = request.data.get('group_ids')
        group = Group.objects.create(name=group_name)
        try:
            qs = Group.objects.get(id=group_ids[0]).user_set.all()
            for group_id in group_ids[1:]:
                qs = qs.union(Group.objects.get(id=group_id).user_set.all())
        except ObjectDoesNotExist:
            group.delete()
            return Response(f'Group with id {group_id} does not exist, please, try again', status=ST_400)
        group.user_set.set(qs)
        return Response(group_successfully_created, status=ST_201)


class GroupIntersection(generics.CreateAPIView):
    permission_classes = (UserIsStaff,)

    def create(self, request, *args, **kwargs):
        group_name = request.data.get('group_name')
        group_ids = request.data.get('group_ids')
        group = Group.objects.create(name=group_name)
        try:
            qs = Group.objects.get(id=group_ids[0]).user_set.all()
            for group_id in group_ids[1:]:
                qs = qs.intersection(Group.objects.get(
                    id=group_id).user_set.all())
        except ObjectDoesNotExist:
            group.delete()
            return Response(f'Group with id {group_id} does not exist, please, try again', status=ST_400)
        group.user_set.set(qs)
        return Response(group_successfully_created, status=ST_201)


class GroupDifference(generics.CreateAPIView):
    permission_classes = (UserIsStaff,)

    def create(self, request, *args, **kwargs):
        group_name = request.data.get('group_name')
        group_ids = request.data.get('group_ids')
        group = Group.objects.create(name=group_name)
        try:
            qs = Group.objects.get(id=group_ids[0]).user_set.all()
            for group_id in group_ids[1:]:
                qs = qs.difference(Group.objects.get(
                    id=group_id).user_set.all())
        except ObjectDoesNotExist:
            group.delete()
            return Response(f'Group with id {group_id} does not exist, please, try again', status=ST_400)
        group.user_set.set(qs)
        return Response(group_successfully_created, status=ST_201)
