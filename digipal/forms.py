from django import forms
from django.forms import ModelForm
from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import FilteredSelectMultiple
from models import Allograph, Hand, Status, Character, Feature, Component, Aspect, Repository, Scribe, Place, Date, HistoricalItem, Institution, Component, Feature
from models import Script, CurrentItem
import urllib2

class OnlyScribe(forms.Form):
    status_list = Status.objects.filter(default=True)
    scribe = forms.ModelChoiceField(queryset = Scribe.objects.all())

class ScribeAdminForm(forms.Form):

    allograph = forms.ModelChoiceField(queryset=Allograph.objects.all())
    component = forms.ModelChoiceField(queryset=Component.objects.all())
    #feature = forms.ModelChoiceField(queryset=Feature.objects.all(), widget=SelectMultiple)


class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField()
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)

class AllographSelect(Select):
    '''Special variant of the Select widget which adds a class to each option.
        The class contains the id of the type of the ontograph linked to the allograph.
        e.g.
            <option value="42">r, Caroline</option>
            =>
            <option class="type-2" value="42">r, Caroline</option>

        Because allograph 42 derives from an ontograph of type = 2
    '''
    def render_option(self, selected_choices, option_value, option_label):
        ret = super(AllographSelect, self).render_option(selected_choices, option_value, option_label)
        if option_value:
            a = Allograph.objects.get(id=int(option_value))
            ret = ret.replace('<option ', '<option class="type-%s" ' % a.character.ontograph.ontograph_type.id)
        return ret

class ImageAnnotationForm(forms.Form):
    status_list = Status.objects.filter(default=True)

    if status_list:
        default_status = status_list[0]

    #status = forms.ModelChoiceField(queryset=Status.objects.all(),
    #        initial=default_status)
    hand = forms.ModelChoiceField(required=False, queryset=Hand.objects.all(),
        widget = Select(attrs={'name': 'hand', 'class':'chzn-select hand_form', 'data-placeholder':"Hand"}),
        label = "",
        empty_label = '------',
        )
    #after = forms.ModelChoiceField(required=False,
    #        queryset=Allograph.objects.all())
    allograph = forms.ModelChoiceField(required=False, queryset=Allograph.objects.all(),
        widget = AllographSelect(attrs={'name': 'allograph', 'class':'chzn-select allograph_form', 'data-placeholder':"Allograph"}),
        label = "",
        empty_label = '------',
    )
    #before = forms.ModelChoiceField(required=False,
    #        queryset=Allograph.objects.all())
    #feature = forms.MultipleChoiceField(required=False,
    #        widget=forms.SelectMultiple(attrs={'size': 25}))
    display_note = forms.CharField(required=False,
                                   label = "",
            widget=Textarea(attrs={'cols': 25, 'rows': 5, 'class':'hidden'}))
    internal_note = forms.CharField(required=False,
                                    label = "",
            widget=Textarea(attrs={'cols': 25, 'rows': 5, 'class':'hidden'}))

    def clean(self):
        """The feature field is always marked as invalid because the choices
        are populated dinamically on the client side, therefore the clean
        method needs to be overriden to ignore errors related to the feature
        field."""
        super(ImageAnnotationForm, self).clean()

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


from digipal.models import Image

class FilterManuscriptsImages(forms.Form):

    town_or_city = forms.ModelChoiceField(
        queryset = Place.objects.filter(repository__currentitem__itempart__images__isnull=False).distinct().values_list('name', flat=True).order_by('name'),
        widget = Select(attrs={'id':'town-select', 'class':'chzn-select', 'data-placeholder':"Choose a Town or City"}),
        label = "",
        empty_label = "Town or City",
        required = False)

    repository = forms.ChoiceField(
        choices = [("", "Repository")] + [(m.human_readable(), m.human_readable()) for m in Repository.objects.filter(currentitem__itempart__images__id__gt=0).order_by('place__name', 'name').distinct()],
        widget = Select(attrs={'id':'repository-select', 'class':'chzn-select', 'data-placeholder':"Choose a Repository"}),
        label = "",
        required = False)

    date = forms.ModelChoiceField(
        #queryset = Date.objects.filter().values_list('date', flat=True).order_by('date').distinct(),
        # TODO: order the dates
        queryset = Image.objects.values_list('hands__assigned_date__date', flat=True).order_by('hands__assigned_date__date').distinct(),
        widget = Select(attrs={'id':'date-select', 'class':'chzn-select', 'data-placeholder':"Choose a Date"}),
        label = "",
        empty_label = "Date",
        required = False)

    # page size
    pgs = forms.CharField(
        initial=10,
        required=False,
        label='',
        widget=HiddenInput())

def get_search_terms_classes():
    ret = ''
    from mezzanine.conf import settings
    if getattr(settings, 'AUTOCOMPLETE_PUBLIC_USER', True):
        ret = ' autocomplete '
    return ret

class SearchPageForm(forms.Form):
    """ Represents the input form on the search page """

    def __init__(self, *args, **kwargs):
        # set basic_search_type: 'hands' by default if not selected
        if not args:
            args = [{}]
        else:
            args = list(args)[:]
            args[0] = args[0].copy()
#         if 'basic_search_type' not in args[0]:
#             args[0]['basic_search_type'] = 'manuscripts'
        if 's' not in args[0]:
            args[0]['s'] = '1'
        super(SearchPageForm, self).__init__(*args, **kwargs)

    terms = forms.CharField(
        label='',
        required=False,
        error_messages={
        'required': 'Please enter at least one search term',
        'invalid': 'Enter a valid value'},
        widget=TextInput(attrs={
            'id': 'search-terms',
            #'class':'textEntry form-control',
            'class':'form-control ' + get_search_terms_classes(),
            'placeholder': 'Enter search terms',
            #'required': 'required',
            "autocomplete":"off"})
    )
    basic_search_type = forms.CharField(
        label='',
        required=False,
        widget=HiddenInput(attrs={'id':'basic_search_type'}),
        initial='',
    )
    from_link = forms.BooleanField(
        initial=False,
        required=False,
        label='advanced',
        widget=HiddenInput(attrs={'id':'advanced'})
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
        widget=HiddenInput(attrs={'id':'active_years'})
    )
    result_type = forms.CharField(
        initial='',
        required=False,
        widget=HiddenInput()
    )
    s = forms.CharField(
        required=False,
        label='',
        widget=HiddenInput()
    )
    # page size
    pgs = forms.CharField(
        initial=10,
        required=False,
        label='',
        widget=HiddenInput()
    )

