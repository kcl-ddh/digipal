from digipal.models import ItemPart, GraphComponent, IdiographComponent, Idiograph, Hand, Graph, Image

def count():
	context = {
		'manuscripts': ItemPart.objects.count(),
		'images': Image.objects.count(),
		# see JIRA 433
		'features': GraphComponent.features.through.objects.count() + IdiographComponent.features.through.objects.count(),
		'graphs': Graph.objects.count(),
		'idiographs': Idiograph.objects.count(),
		'hands': Hand.objects.count()
	}
	return context