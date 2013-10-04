# Create your views here.
from django.template import RequestContext
from django.shortcuts import render_to_response
# Object models
from digipal.models import Graph


def cookied_inputs(request):
    context = {'test': 'Yo!'}
    
    

    return render_to_response('test/cookied_inputs.html', context,
            context_instance=RequestContext(request))
