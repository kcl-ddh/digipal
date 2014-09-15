from digipal.models import Annotation
from django.db.models.signals import post_delete
from django.db import transaction

'''JIRA DIGIPAL-523: Check orphan graph records.
   Make sure the graph records won't survive without an annotation.
   Without this event, deleting an image or an annotation 
   would leave orphan graph records.
'''

@transaction.atomic
def post_delete_annotation(sender, **kwargs):
    annotation = kwargs['instance']
    if annotation and annotation.graph:
        annotation.graph.delete()

def init_signals():
    post_delete.connect(post_delete_annotation, sender=Annotation, dispatch_uid="digipal.signals.annotation.post_delete")
