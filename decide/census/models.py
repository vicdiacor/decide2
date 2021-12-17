from django.db import models
from django.contrib.auth.models import Group
from enum import Enum

class Census(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()
    adscripcion = models.TextField()

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)

class ParentGroup(Group):
    isPublic = models.BooleanField(default=False)

class RequestStatus(Enum):
        ACCEPTED = 'ACCEPTED' 
        REJECTED = 'REJECTED'
        PENDING = 'PENDING'
        @classmethod
        def choices(cls):
            return tuple((i.name, i.value) for i in cls)
class Request(models.Model):
    voter_id = models.PositiveIntegerField()
    group_id = models.PositiveIntegerField()
    status = models.CharField(max_length=255, choices=RequestStatus.choices(), default=RequestStatus.PENDING)