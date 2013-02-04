from digipal.forms import FacetForm
from haystack.views import FacetedSearchView, search_view_factory
from haystack.query import SearchQuerySet
from digipal.models import CurrentItem, Hand

def facet_search(request, model):
    """
    Build a thread-safe faceted search view
    This view replaces the officially-documented confusing insanity,
    which places a lot of logic in urls.py

    New faceted searches should only require a new entry in the 'queries' dict
    for the model in question, and a new template with minor modifications to
    render the model result table correctly

    The search sequence is as follows:
    1. Select a SearchQuerySet from the 'queries' dict based on the model param
    2. Call FacetForm.search(), which performs narrowing and querying
    3. Return the results to FacetView.extra_context() to add context vars
    4. Render the template with the resulting facet and page objects

    This rewrite was inspired by: http://stackoverflow.com/q/10469340/416626
    """
    queries = {
        'hand': SearchQuerySet().facet(
            "assigneddate").facet(
            "assignedplace").facet(
            "currentitem").facet(
            "historicalitem").facet(
            "scribe").facet(
            "idiograph").facet(
            "allograph").facet(
            "character").models(Hand),
        'manuscript': SearchQuerySet().facet(
            "assigneddate").facet(
            "assignedplace").facet(
            "currentitem").facet(
            "historicalitem").facet(
            "scribe").facet(
            "idiograph").facet(
            "allograph").facet(
            "character").models(CurrentItem),
    }
    sqs = queries.get(model)
    view = search_view_factory(
        view_class=FacetView,
        template='search/search.html',
        searchqueryset=sqs,
        form_class=FacetForm
        )
    # call FacetForm.search(), and return request context to FacetView
    return view(request)


class FacetView(FacetedSearchView):
    """
    For faceted searching
    """
    def __name__(self):
        return "FacetView"

    def build_form(self, form_kwargs=None):
            """
            Instantiates the form the class should use to process the search query
            You can swap out GET for POST here, and make the data dict mutable
            """
            data = None
            kwargs = {
                'load_all': self.load_all,
            }
            if form_kwargs:
                kwargs.update(form_kwargs)

            if len(self.request.GET):
                data = self.request.GET
                # make it mutable
                intermediate = data.copy()
                # don't pass any blank facets to the search method
                for key, value in intermediate.items():
                    if not value:
                        del(intermediate[key])
                data = intermediate

            if self.searchqueryset is not None:
                # update a blank query here
                kwargs['searchqueryset'] = self.searchqueryset

            # can we get the facets and pass them as kwargs?
            return self.form_class(data, **kwargs)

    def extra_context(self):
        """ Add active and available facets to request context """
        extra = super(FacetedSearchView, self).extra_context()
        extra['active_facets'] = dict()
        if self.results == []:
            extra['facets'] = self.form.search().facet_counts()
        else:
            narrowed_by = list()
            try:
                # build the active facets dict if facets have been selected
                assert self.results.query.narrow_queries
                for each in list(self.results.query.narrow_queries):
                    narrowed_by.append(each)
                # remove the 'q' key
                narrowed_by.pop()
                extra['active_facets'] = [
                    n.split('_')[0] + ':' + n.split(':')[-1] for n in narrowed_by]
            except AssertionError:
                pass
            extra['facets'] = self.results.facet_counts()
        # finally, return template and extra context as a response
        return extra
