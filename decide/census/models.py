from django.db import models
from django.contrib.auth.models import Group

class Census(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()
    adscripcion = models.TextField()

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)

class ParentGroup(Group):
    isPublic = models.BooleanField(default=False)

    