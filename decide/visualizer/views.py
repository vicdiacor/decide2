import json
from django.views.generic import TemplateView
from django.conf import settings
from django.http import Http404
from voting.models import Voting
from django.contrib.auth.models import Group

from base import mods

def get_statistics_from_voting(voting_id: int):
    votes = Voting.objects.filter(id=voting_id)
    res = dict()
    return res

class VisualizerView(TemplateView):
    template_name = 'visualizer/visualizer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vid = kwargs.get('voting_id', 0)

        try:
            r = mods.get('voting', params={'id': vid})
            context['voting'] = json.dumps(r[0])
            context['statistics'] = get_statistics_from_voting(vid)
        except:
            raise Http404

        return context
