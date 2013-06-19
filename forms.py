from django import forms
from django.forms import ModelForm
from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import FilteredSelectMultiple
from models import Allograph, Hand, Status, Character, Feature, Component, Aspect, Repository, Scribe, Place, Date, HistoricalItem, Institution, Component, Feature
from models import Script, CurrentItem
from haystack.forms import FacetedSearchForm
from haystack.query import SearchQuerySet
from haystack.inputs import Exact, AutoQuery
import urllib2

class OnlyScribe(forms.Form):
    status_list = Status.objects.filter(default=True)
    scribe = forms.ModelChoiceField(queryset = Scribe.objects.all())

class ScribeAdminForm(forms.Form):

    allograph = forms.ModelChoiceField(queryset=Allograph.objects.all())
    component = forms.ModelChoiceField(queryset=Component.objects.all())
    feature = forms.ModelChoiceField(queryset=Feature.objects.all(), widget=SelectMultiple)


class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField()
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)

class PageAnnotationForm(forms.Form):
    status_list = Status.objects.filter(default=True)

    if status_list:
        default_status = status_list[0]

    status = forms.ModelChoiceField(queryset=Status.objects.all(),
            initial=default_status)
    hand = forms.ModelChoiceField(queryset=Hand.objects.all())
    after = forms.ModelChoiceField(required=False,
            queryset=Allograph.objects.all())
    allograph = forms.ModelChoiceField(queryset=Allograph.objects.all())
    before = forms.ModelChoiceField(required=False,
            queryset=Allograph.objects.all())
    feature = forms.MultipleChoiceField(required=False,
            widget=forms.SelectMultiple(attrs={'size': 25}))
    display_note = forms.CharField(required=False,
            widget=Textarea(attrs={'cols': 25, 'rows': 5}))
    internal_note = forms.CharField(required=False,
            widget=Textarea(attrs={'cols': 25, 'rows': 5}))

    def clean(self):
        """The feature field is always marked as invalid because the choices
        are populated dinamically on the client side, therefore the clean
        method needs to be overriden to ignore errors related to the feature
        field."""
        super(PageAnnotationForm, self).clean()

        if 'feature' in self._errors:
            del self._errors['feature']

        return self.cleaned_data


class InlineLinkWidget(forms.Widget):
    """This widget adds a link, to edit the current inline, after the inline
    form fields."""
    def __init__(self, obj, attrs=None):
        self.object = obj
        super(InlineLinkWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        if self.object.pk:
            return mark_safe(u'<a onclick="return showRelatedObjectLookupPopup(this);" href="../../../%s/%s/%s/">%s</a>' % \
                    (self.object._meta.app_label,
                        self.object._meta.object_name.lower(),
                        self.object.pk, self.object))
        else:
            return mark_safe(u'')


class InlineForm(forms.ModelForm):
    """This form renders a model and adds a link to edit the nested inline
    model. This is useful for inline editing when the nested inline fields are
    not displayed."""
    # required=False is essential because we don't render input tag so there
    # will be no value submitted.
    edit_link = forms.CharField(label='Edit', required=False)

    class Meta:
        exclude = ()
        fieldsets = []

    def __init__(self, *args, **kwargs):
        super(InlineForm, self).__init__(*args, **kwargs)
        # instance is always available, it just does or doesn't have pk.
        self.fields['edit_link'].widget = InlineLinkWidget(self.instance)




class FilterHands(forms.Form):
    scribes = forms.ModelChoiceField(
        queryset = Scribe.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'scribes-select', 'class':'chzn-select', 'data-placeholder':'Choose a Scribe'}),
        label = "",
        empty_label = "Scribe",
        required = False)

    repository = forms.ChoiceField(
        choices = [("", "Repository")] + [(m.name, m.human_readable()) for m in Repository.objects.all().order_by('name').distinct()],
        label = "",
        required = False,
        widget = Select(attrs={'id':'placeholder-select', 'class':'chzn-select', 'data-placeholder':"Choose a Repository"}),
        initial = "Repository",
    )


    place = forms.ModelChoiceField(
        queryset = Place.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'place-select', 'class':'chzn-select', 'data-placeholder':"Choose a Place"}),
        label = "",
        empty_label = "Place",
        required = False)

    date = forms.ModelChoiceField(
        queryset = Date.objects.values_list('date', flat=True).order_by('date').distinct(),
        widget = Select(attrs={'id':'date-select', 'class':'chzn-select', 'data-placeholder':"Choose a Date"}),
        label = "",
        empty_label = "Date",
        required = False)

class FilterManuscripts(forms.Form):

    index = forms.ModelChoiceField(
        queryset = HistoricalItem.objects.values_list('catalogue_number', flat=True).distinct(),
        widget = Select(attrs={'id':'index-select', 'class':'chzn-select', 'data-placeholder':"Choose an Index"}),
        label = "",
        empty_label = "Index",
        required = False)

    repository = forms.ChoiceField(
        choices = [("", "Repository")] + [(m.name, m.human_readable()) for m in Repository.objects.all().order_by('name').distinct()],
        label = "",
        required = False,
        widget = Select(attrs={'id':'placeholder-select', 'class':'chzn-select', 'data-placeholder':"Choose a Repository"}),
        initial = "Repository",
    )

    date = forms.ModelChoiceField(
        queryset = Date.objects.values_list('date', flat=True).order_by('date').distinct(),
        widget = Select(attrs={'id':'date-select', 'class':'chzn-select', 'data-placeholder':"Choose a Date"}),
        label = "",
        empty_label = "Date",
        required = False)

class FilterManuscriptsImages(forms.Form):

    town_or_city = forms.ModelChoiceField(
        queryset = Place.objects.filter(repository__currentitem__itempart__pages__isnull=False).distinct().values_list('name', flat=True),
        widget = Select(attrs={'id':'town-select', 'class':'chzn-select', 'data-placeholder':"Choose a Town or City"}),
        label = "",
        empty_label = "Medieval Town or City",
        required = False)

    
    repository = forms.ChoiceField(
        choices = [("", "Repository")] + [(m.name, m.human_readable()) for m in Repository.objects.all().order_by('name').distinct()],
        widget = Select(attrs={'id':'repository-select', 'class':'chzn-select', 'data-placeholder':"Choose a Repository"}),
        label = "",
        required = False)

    date = forms.ModelChoiceField(
        queryset = Date.objects.values_list('date', flat=True).order_by('date').distinct(),
        widget = Select(attrs={'id':'date-select', 'class':'chzn-select', 'data-placeholder':"Choose a Date"}),
        label = "",
        empty_label = "Date",
        required = False)

class FilterScribes(forms.Form):
    name = forms.ModelChoiceField(
        queryset = Scribe.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'name-select', 'class':'chzn-select', 'data-placeholder':"Choose a Name"}),
        label = "",
        empty_label = "Name",
        required = False)

    scriptorium = forms.ModelChoiceField(
        queryset = Institution.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'scriptorium-select', 'class':'chzn-select', 'data-placeholder':"Choose a Scriptorium"}),
        empty_label = "Scriptorium",
        label = "",
        required = False)

    date = forms.ModelChoiceField(
        queryset = Date.objects.values_list('date', flat=True).order_by('date').distinct(),
        widget = Select(attrs={'id':'date-select', 'class':'chzn-select', 'data-placeholder':"Choose a Date"}),
        label = "",
        empty_label = "Date",
        required = False)

    character = forms.ModelChoiceField(
        queryset = Character.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'character-select', 'class':'chzn-select', 'data-placeholder':"Choose a Character"}),
        label = "",
        empty_label = "Character",
        required = False)

    component = forms.ModelChoiceField(
        queryset = Component.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'component-select', 'class':'chzn-select', 'data-placeholder':"Choose a Component"}),
        label = "",
        empty_label = "Component",
        required = False)

    feature = forms.ModelChoiceField(
        queryset = Feature.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'feature-select', 'class':'chzn-select', 'data-placeholder':"Choose a Feature"}),
        label = "",
        empty_label = "Feature",
        required = False)

class SearchPageForm(forms.Form):
    """ Represents the input form on the search page """
    
    def __init__(self, *args, **kwargs):
        # set basic_search_type: 'hands' by default if not selected
        if not args:
            args = [{}]
        else:
            args = list(args)[:]
            args[0] = args[0].copy()
        if 'basic_search_type' not in args[0]:
            args[0]['basic_search_type'] = 'hands'
        super(SearchPageForm, self).__init__(*args, **kwargs)
 
    terms = forms.CharField(
        label='',
        required=False,
        error_messages={
        'required': 'Please enter at least one search term',
        'invalid': 'Enter a valid value'},
        widget=TextInput(attrs={
            'id': 'search-terms', 
            'class':'textEntry',
            'placeholder': 'Enter search terms',
            'required': 'required',
            "autocomplete":"off"})
    )
    basic_search_type = forms.ChoiceField(
        label='',
        #required=True,
        #error_messages={'required': 'Please select something to search for'},
        required=False,
        widget=forms.RadioSelect(),
        choices = [
                ('hands', 'Hands'),
                ('manuscripts', 'Manuscripts'),
                ('scribes', 'Scribes')],
        initial='hands',
#             attrs={'required': 'required'}),
    )
    ordering = forms.CharField(
        initial="default",
        required=False,
        label='ordering',
        widget=HiddenInput(attrs={'id':'active_ordering'})
    )
 
    years = forms.CharField(
        initial='1000-1300',
        required=False,
        label='years',
        widget=HiddenInput(attrs={'id':'active_years'}))
 


# class SearchForm(forms.Form):
#     """ Represents the input form on the search page """
# 
#     terms = forms.CharField(
#         label='',
#         required=False,
#         error_messages={
#         'required': 'Please enter at least one search term',
#         'invalid': 'Enter a valid value'},
#         widget=TextInput(attrs={
#             'id': 'textEntry',
#             'class':'textEntry',
#             'placeholder': 'Enter search terms',
#             'required': 'required',
#             "autocomplete":"off"}))
#     basic_search_type = forms.ChoiceField(
#         label='',
#         required=True,
#         error_messages={'required': 'Please select something to search for'},
#         widget=forms.RadioSelect(attrs={
#             'required': 'required'}),
#         choices = [
#             ('hands', 'Hands'),
#             ('manuscripts', 'Manuscripts'),
#             ('scribes', 'Scribes')],
#         initial='hands'
#         )
#     ordering = forms.CharField(
#         initial="default",
#         required=False,
#         label='ordering',
#         widget=HiddenInput(attrs={'id':'active_ordering'}))
# 
#     years = forms.CharField(
#         initial='1000-1300',
#         required=False,
#         label='years',
#         widget=HiddenInput(attrs={'id':'active_years'}))
# 
# class QuickSearch(forms.Form):
#     terms = forms.CharField(
#         label='',
#         required=True,
#         error_messages={
#         'required': 'Please enter at least one search term',
#         'invalid': 'Enter a valid value'},
#         widget=TextInput(attrs={
#             'id': 'input',
#             'class':'textEntry',
#             'placeholder': 'Enter search terms',
#             'required': 'required',
#             "autocomplete":"off"}))



class DrilldownForm(forms.Form):
    """ Represents the Hand drill-down form on the search results page """
    script_select = forms.ModelChoiceField(
        queryset=Script.objects.values_list('name', flat= True).order_by('name').distinct(),
        widget=Select(attrs={'id':'script-select', 'class':'chzn-select', 'data-placeholder':"Choose a Script"}),
        label="",
        empty_label = "Script",
        required=False)
    character_select = forms.ModelChoiceField(
        queryset=Character.objects.values_list('name', flat= True).order_by('name').distinct(),
        widget=Select(attrs={'id':'character-select', 'class':'chzn-select', 'data-placeholder':"Choose a Character"}),
        label='',
        empty_label = "Character",
        required=False)
    allograph_select = forms.ChoiceField(
        choices = [("", "Allograph")] + [(m.name, m.human_readable()) for m in Allograph.objects.all().order_by('name').distinct()],
        #queryset=Allograph.objects.values_list('name', flat= True).order_by('name').distinct(),
        widget=Select(attrs={'id':'allograph-select', 'class':'chzn-select', 'data-placeholder':"Choose an Allograph"}),
        label='',
        required=False)
    component_select = forms.ModelChoiceField(
        queryset=Component.objects.values_list('name', flat= True).order_by('name').distinct(),
        widget=Select(attrs={'id':'component-select', 'class':'chzn-select', 'data-placeholder':"Choose a Component"}),
        empty_label = "Component",
        label='',
        required=False)
    feature_select = forms.ModelChoiceField(
        queryset=Feature.objects.values_list('name', flat= True).order_by('name').distinct(),
        widget=Select(attrs={'id':'feature-select', 'class':'chzn-select', 'data-placeholder':"Choose a Feature"}),
        empty_label = "Feature",
        label='',
        required=False)
    # hidden field which we populate with the existing search term in the view
    terms = forms.CharField(
      required=False,
      label='terms',
      widget=HiddenInput(),
      )

    # def __init__(self, scribe):
    #     super(DrilldownForm, self).__init__()
    #     self.fields['allograph_select'].queryset = Allograph.objects.filter(
    #         scribe=scribe)


class FacetForm(FacetedSearchForm):
    """ Faceting """
    # TODO: do kwargs from FacetView.build_form arrive here as self.kwarg?
    q = forms.CharField(
    label='',
    required=False,
    error_messages={'required': 'Please enter at least one search term'},
    widget=TextInput(attrs={
        'class':'textEntry',
        'required': 'required',
        'placeholder': 'Enter search terms'}))

    # TODO add fields based on searchqueryset?

    def search(self):
        """
        This method is called upon form submission
        Remember that 'data' is a QueryDict, and its items() method is specific

        """
        cleaned_facets = list()
        # faceting expects fieldnames in fieldname_exact:value format
        # we never want these keys in our facet function
        to_exclude = (
            'q',
            'page',
            'csrfmiddlewaretoken',
            "")
        combined = list
        if self.data:
            for each in self.data.lists():
                if each[0] not in to_exclude:
                    for remainder in each[1]:
                        cleaned_facets.append(each[0] + "_exact:" + remainder)
            self.selected_facets = list(set(cleaned_facets))

        sqs = super(FacetedSearchForm, self).search()

        if not self.is_valid():
            # invalid / no search term, or initial GET, return all results
            sqs = self.searchqueryset.all()
            for facet in self.selected_facets:
                sqs = sqs.narrow(facet)
        else:
            sqs = self.searchqueryset
            # narrow by each selected facet
            for facet in self.selected_facets:
                sqs = sqs.narrow(facet)
            # perform auto-query using search term if it exists
            if self.cleaned_data.get('q'):
                sqs = sqs.filter(content=AutoQuery(self.cleaned_data['q']))
            # TODO: see if we can convert available facet dicts to OrderedDict
            # and sort them however we want
        if self.load_all:
            sqs = sqs.load_all()
        # return sqs to FacetView.extra_context
        return sqs
