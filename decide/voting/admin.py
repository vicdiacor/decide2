from django.contrib import admin
from django.utils import timezone

from .models import QuestionOption
from .models import Question
from .models import Voting

from .filters import StartedFilter

from django.contrib.auth.models import User, Group
from census.models import Census



def start(modeladmin, request, queryset):
    for v in queryset.all():
        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()


def stop(ModelAdmin, request, queryset):
    for v in queryset.all():
        v.end_date = timezone.now()
        v.save()


def tally(ModelAdmin, request, queryset):
    for v in queryset.filter(end_date__lt=timezone.now()):
        token = request.session.get('auth-token', '')
        v.tally_votes(token)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption


class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionOptionInline]


class VotingAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    readonly_fields = ('start_date', 'end_date', 'pub_key',
                       'tally', 'postproc')
    date_hierarchy = 'start_date'
    list_filter = (StartedFilter,)
    search_fields = ('name', )

    actions = [ start, stop, tally ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        groups = obj.groups

        # Comprueba que el id del grupo no es null o blank
        if (groups != '' and groups!=None): 
            groupsIds = list(groups.split(','))

        # Obtener todos los usuarios que pertenecen al grupo
            for id in groupsIds:
                group = Group.objects.get(pk=int(id))
                voters = User.objects.filter(groups=group)

                # Por cada usuario
                # Añadir al censo de dicha votación
                voting_id = Voting.objects.get(name=obj.name).pk
                for voter in voters:
                    census = Census(voting_id=voting_id, voter_id=voter.pk)
                    census.save()


admin.site.register(Voting, VotingAdmin)
admin.site.register(Question, QuestionAdmin)
