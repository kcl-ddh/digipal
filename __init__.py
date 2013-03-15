# Tell South about the iipimage field
# See http://south.readthedocs.org/en/latest/tutorial/part4.html#simple-inheritance
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^iipimage\.fields\.ImageField"])
