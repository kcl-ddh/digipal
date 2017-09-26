import re
from digipal import utils
from digipal.utils import inc_counter, sorted_natural
from digipal.utils import get_range_from_date, MAX_DATE_RANGE


def draw_overview(faceted_search, context, request):
    view = Overview(faceted_search, context, request)
    view.draw()


class Query(object):
    def __init__(self, index=0):
        self.index = index
        self.is_active = 0
        self.is_valid = 0
        self.faceted_search = None
        self.request = None

    def get_records(self):
        if self.index == 0:
            return self.faceted_search.overview_all_records
        else:
            return self.faceted_search.overview_records

    def get_count(self):
        records = self.get_records()
        if isinstance(records, list):
            ret = len(records)
        else:
            ret = records.count()
        return ret

    def get_summary(self):
        ret = 'Summary for query %s' % self.index
        if self.index == 0:
            ret = 'All records'
        else:
            if self.faceted_search:
                ret = self.faceted_search.get_summary(self.request, True)
        if self.faceted_search:
            ret = '%s : %s' % (self.faceted_search.get_label(), ret)
        return ret

    def get_color(self):
        # colors = ['#A0A0A0', '#a1514d', 'blue', 'green', 'orange', '#A000A0',
        # '#00A0A0']
        colors = ['#C0C0C0', '#6060FF', '#60FF60',
                  '#FF8080', 'orange', '#A000A0', '#00A0A0']
        return colors[self.index]

    def get_index(self):
        return self.index

    def set_active(self, is_active):
        self.is_active = is_active

    def is_active(self):
        return self.is_active

    def get_remove_link(self):
        ret = '?'
        for k, v in self.request_current.GET.iteritems():
            if k.startswith('q%s_' % self.index):
                continue
            ret += '&%s=%s' % (k, v)
        return ret

    def set_from_request(self, request, faceted_search):
        '''
        Query 0: a full search on the currently selected result type (always there)
        Query 1: the current result set (but if it's a full search, it is invalidated)
        Query 2, ...: the query saved in the query string. qi_X=Y
        '''
        if self.index < 1:
            self.is_valid = 1
        if self.index == 1:
            if not faceted_search.is_full_search():
                self.is_valid = 1

        index = utils.get_int_from_request_var(request, 'qi', 1)
        if self.index == index:
            self.is_active = 1

        self.request = request
        self.request_current = request
        if request.GET.get('q%s_result_type' % (self.index), ''):
            self.is_valid = 1

        self.is_hidden = utils.get_int_from_request_var(
            request, 'q%s_hidden' % self.index, 0)

        # if self.is_active:
        if self.index < 2:
            self.faceted_search = faceted_search
        else:
            from digipal.views.faceted_search.faceted_search import simple_search

            new_url = '/?'
            url_is_set = False
            for k, v in self.request.GET.iteritems():
                if k.startswith('q%s_' % self.index):
                    new_url += '&%s=%s' % (k.replace('q%s_' %
                                                     self.index, ''), v)
                    url_is_set = True

            if url_is_set:
                from django.test.client import RequestFactory
                request = RequestFactory().get(new_url)
                user = self.request.user
                self.request = request
                self.request.user = user

                self.faceted_search = simple_search(request)


class Queries(object):
    def __init__(self, request, context, faceted_search):
        '''Instantiate all the queries from the query string'''
        self.request = request
        self.context = context
        self.faceted_search = faceted_search

        self.queries = []

        i = 0
        while True:
            query = self.get_query_from_request(i)
            if query:
                self.queries.append(query)
            else:
                if i > 1:
                    break
            i += 1

    def get_query_from_request(self, index=0):
        ret = Query(index)
        ret.set_from_request(self.request, self.faceted_search)

        if not ret.is_valid:
            ret = None

        return ret

    def get_copy_link(self):
        ret = '?'
        for k, v in self.request.GET.iteritems():
            ret += '&%s=%s' % (k, v)
            if not re.match(ur'^q\d+_.*$', k):
                ret += '&q%s_%s=%s' % (len(self.queries), k, v)
        return ret

    def get_queries(self):
        return self.queries

    def get_hidden_inputs(self):
        ret = ''
        for k, v in self.request.GET.iteritems():
            if re.match(ur'^q\d+_.*$', k):
                from django.utils.html import escape
                ret += u'<input type="hidden" name="%s" value="%s" />' % (
                    escape(k), escape(v))
        return ret


class Overview(object):
    '''
        IN
            faceted_search
            context
            request

        OUT
            Visualisation of faceted search results on a TIMELINE.
            Where each result is encoded as a DATA POINT and display as a hor. BAR
            Data points/bars can be CONFLATED/COLLAPSED by document/IP/HI
            The bars are STACKED DOWN and
            arranged vertically into BANDS, where each band is a separate option
            in a given facet.

            The unit for the coordinates are:
                X: one year
                Y: height of one bar
            These are not pixel coordinates. The pixel coordinates are calulated
            on client side using a scaling factor based on the desired canvas size.

            context =

            vcat = { e.g. faceted field for document type }
            vcats = [ list of faceted field for the drop down ]
            canvas:
                font_size
                width
                height
                drawing
                    points:
                        [
                            [[x1, x2], y, found, label, url, conflatedid, annotation]
                            [
                                0: [x1, x2],
                                1: ys,
                                2: set([query.index]),
                                3: label,
                                4: record.get_absolute_url(),
                                5: conflateid,
                                6: URL annotation,
                            ]
                            ...
                        ]
                    point_height: 7
                    x:
                        # x, y, label
                        [[0, 2000, '1000'], [10, 2000, '1010'], ...]]
                    y:
                        # x, y, label
                        []

    '''

    def __init__(self, faceted_search, context, request):
        # if True, we group all the results by document to avoid stacking
        # graphs or clauses
        self.faceted_search = faceted_search
        self.settings = self.faceted_search.settings.getGlobal('visualisation')

        self.context = context
        self.request = request
        # an index used to detect data point overlap and create stack
        # [y][[x0, x1], [x0, x1]]
        self.stack = {}

        self.cat_hits = {}
        self.font_size = 12
        # margin on each side of a label (in pixels)
        self.margin = 3
        self.font_size_margin = self.font_size + 2 * self.margin
        self.bar_height = utils.get_int_from_request_var(request, 'vz_bh', 7)
        self.graph_size = utils.get_int_from_request_var(request, 'vz_gs', 40)

        context['viz'] = {}
        context['viz']['vz_bh'] = self.bar_height
        context['viz']['vz_gs'] = self.graph_size

        self.mins = [None, None]
        self.maxs = [None, None]
        # histogram at the bottom of the chart with the sum of all the ocurrences
        # above
        # format = {0: {0: 3, 1: 2}, 1: {0:2, 1:1}, ... }
        # format = {X/year: {layer index: bar count, layer index: bar count,
        # ...}, ...}
        self.histogram = {}
        self.histogram_height = 0

        self.band_width = 1000000

    def draw(self):
        '''
            Write the drawing information on the context for the view to
            generate the visualisation.
        '''
        if self.faceted_search.get_selected_view()['key'] != 'overview':
            return

        self.init_queries()

        # TODO: MoA, use:
        # self.set_conflate('item_part')
        # self.set_x_field_key('hi_date')
        # EXON
        # self.set_x_field_key('locus')
        # self.set_conflate('unitid')

        self.set_x_field_key(self.settings['field_x'])
        self.set_conflate(self.settings['field_conflate'])

        # self.set_fields()

        self.set_points()

        if self.points:
            self.draw_internal()

            self.compact_bands()

            self.reframe()

    def init_queries(self):
        self.queries = Queries(self.request, self.context, self.faceted_search)
        self.context['queries'] = self.queries

    def set_conflate(self, conflate):
        '''Returns the model represented by a bar (e.g. Graph, ItemPart)'''
#         model = self.faceted_search.get_model()
#         self.conflate = ''
#         if conflate:
#             # get any field with the conflate part
#             for field in self.faceted_search.get_fields():
#                 path = re.replace(conflate, '', field.get('path', ''))
#
#                 if path:
#                     self.conflate = conflate
#                     model, path = self.get_model_from_field(field)
#                     model =
#
#         self.conflate_model = model
        self.conflate = conflate

    def get_conflate_relative_field(self, faceted_search):
        '''Return a new faceted field whith a relative path to the conflated record id'''
        ret = {'path': 'id'}

        if getattr(self, 'conflate', None):
            field = faceted_search.get_field_by_key(self.conflate)
            if field:
                # self.conflate is a field key
                ret['path'] = field['path']
            else:
                # self.conflate is one part of a path (e.g. item_part)
                # let's assume the path is already part of at least one field
                for field in faceted_search.get_fields():
                    m = re.search(
                        ur'(?musi)(.*\.' + re.escape(self.conflate) + ')[._a-z]', field['path'])
                    if m:
                        ret['path'] = m.group(1) + '.id'

        return ret

    def set_points(self):
        '''
            set self.points, an array of data points from one or more result sets.
            Separate results can be conflated into unique data points
            (e.g. graphs into itempart) to simplify visualisation.

            A data point is an array of the form
            [x, y, layers, label, url, conflatedid, image]
        '''
        ret = {}

        self.bands = []

        for query in self.queries.get_queries():
            if query.is_hidden:
                continue
            faceted_search = query.faceted_search

            if not self.set_fields(faceted_search):
                continue

            # TODO: combine multiple results
            # Here we conflate the results and build data points
            # with all info except coordinates.
            conflate_relative_field = self.get_conflate_relative_field(
                faceted_search)

            for record in query.get_records():

                # TODO: self.fields depends on the result type!!!
                # once we allow a mix of result type we'll have to get the
                # fields differently
                conflateid = faceted_search.get_record_field(
                    record, conflate_relative_field)

                point = ret.get(conflateid, None)
                if point is None:
                    point = []

                    # TODO: one request for the whole thing
                    values = []
                    for field in self.fields[:2]:
                        values.append(
                            faceted_search.get_record_field(record, field))

                    x = values[0]

                    # convert x to numerical value
                    if self.fields[0]['type'] == 'date':
                        x = get_range_from_date(x)
                    elif self.fields[0]['key'] == 'locus':
                        # 12v => 25
                        x = self.get_int_from_locus(x)
                    else:
                        # ()TODO: other type than date for x
                        x = 0

                    # turn all x into range
                    if not isinstance(x, list):
                        x = [x, x]

                    ys = values[1]

                    label = faceted_search.get_record_label_html(
                        record, self.request)
                    point = [x, ys, set([query.index]), label,
                             record.get_absolute_url(), conflateid, '']

                    ret[conflateid] = point

                    # determine large y bands for the categories
                    # eg. ['type1', 'type2']
                    if isinstance(ys, list):
                        # flatten it, it may contain nested lists
                        self.bands.extend(ys)
                    else:
                        self.bands.append(ys)

                if query.index > 0:
                    # add layerid
                    point[2].add(query.index)

                    # add annotation to data point
                    from digipal.models import Graph
                    if not point[6] and isinstance(record, Graph):
                        info = record.annotation.get_cutout_url_info(
                            esc=False, rotated=False, fixlen=self.graph_size)
                        point[6] = info['url']

                        # we want to show the label of visible graph
                        point[3] = faceted_search.get_record_label_html(
                            record, self.request)
                        # same with link
                        point[4] = record.get_absolute_url()

        self.points = ret

        return ret

    def draw_internal(self):
        self.context['canvas'] = {'width': 500, 'height': 500}

        self.drawing = {'points': [], 'x': [], 'y': [], 'bar_height': self.bar_height,
                        'font_size': self.font_size, 'label_margin': self.margin}

        points = self.drawing['points']

        self.drawing['colors'] = [query.get_color()
                                  for query in self.queries.get_queries()]
        self.drawing['summaries'] = [query.get_summary()
                                     for query in self.queries.get_queries()]

        # {'agreement': [10, 20]}

        self.init_bands()

        # process all records
        # for record in self.get_all_conflated_ids():
        cat_hit = [0] * len(self.queries.get_queries())
        points_order = sorted(self.points.keys(),
                              key=lambda cid: self.points[cid][0][0])
        # for point in self.points.values():
        for cid in points_order:
            point = self.points[cid]
            found = any(point[2])
            x = point[0]
            ys = point[1]

            # update the min / max x
            if x[0] is not None and x[0] not in MAX_DATE_RANGE and (self.mins[0] is None or self.mins[0] > x[0]):
                self.mins[0] = x[0]
            if x[1] is not None and x[1] not in MAX_DATE_RANGE and (self.maxs[0] is None or self.maxs[0] < x[1]):
                self.maxs[0] = x[1]

            # update histogram
            if 0:
                for xi in range(x[0], x[1] + 1):
                    hist = self.histogram[xi] = self.histogram.get(xi, {})
                    for layer in point[2]:
                        self.histogram_height = max(inc_counter(
                            hist, layer), self.histogram_height)
            else:
                for xi in range(x[0], x[1] + 1):
                    hist = self.histogram[xi] = self.histogram.get(xi, {})
                    layers_key = ','.join(
                        ['%s' % li for li in sorted(point[2])])
                    inc_counter(hist, layers_key)

            # convert y to numerical value
            if not isinstance(ys, list):
                ys = [ys]
            for v in ys:
                y = self.bands.get(v, 0)

                # add the points to the stack
                point[0] = x
                point[1] = y
                # convert layers from set to list to allow json serialisation
                point[2] = list(point[2])

                self.stack_point(point)
                points.append(point)

                # increment hits per category
                self.cat_hits[v] = self.cat_hits.get(v, [0, 0][:])
                self.cat_hits[v][0] += 1
                if found:
                    self.cat_hits[v][1] += 1

    def set_x_field_key(self, x_field_key):
        self.x_field_key = x_field_key

    def get_x_field_key(self):
        return self.x_field_key

    def get_int_from_locus(self, x):
        # returns integer from a locus,
        # e.g. 2v => 2 * 2 + 1
        # returns 0 if not a number (e.g. unumbered)
        n = utils.get_int(re.sub(ur'^(\d+).*$', ur'\1', x), 0) * 2
        if len(x) and 'v' in x[-1]:
            n += 1
        return n

    def set_fields(self, faceted_search):
        '''
            set self.fields = array of faceted fields such that:
                self.fields[0] = field for X dimensions (e.g. { hi_date })
                self.fields[1] = field for bands (e.g. { hi_type } )

            Return True if the fields have been set properly.
                E.g. False if the Content Type has no possible candidate Y field
        '''
        ret = False
        #faceted_search = self.faceted_search
        context = self.context

        possible_categories = self.settings['categories']
        # generate the list of vertical categories
        # we take all the fields of the current result type
        # minus those not found in the global 'categories' list
        # minus those with vcat = False
        context['vcats'] = [field for field in faceted_search.get_fields() if field.get(
            'vcat', True) and (not possible_categories or field['key'] in possible_categories)]

        category_field = faceted_search.get_field_by_key(
            utils.get_request_var(self.request, 'vcat', 'hi_type'))
        if category_field is None:
            category_field = faceted_search.get_field_by_key('hi_type')
        if category_field is None:
            category_field = faceted_search.get_field_by_key('text_type')
        if category_field is None and context['vcats']:
            category_field = context['vcats'][0]

        if category_field:
            context['vcat'] = category_field

            fields = [
                self.get_x_field_key(),
                category_field['key']
            ]

            self.fields = [faceted_search.get_field_by_key(
                field) for field in fields]

            ret = all(self.fields)

        return ret

    def init_bands(self):
        '''
            Initialise the vertical category-bands with a fixed height and label

            set self.bands = {'agreement': 0, 'brieve': 1000, LABEL: TOPY}
        '''
        #value_rankings, self.bands = self.faceted_search.get_field_value_ranking(self.fields[1])

        bands = sorted_natural(list(set(self.bands)))
        # eg. {'type1': 0, 'type2': 1000}
        #self.bands = {self.bands[i]: i*self.band_width for i in range(0, len(self.bands))}
        self.bands = {}
        for i in range(0, len(bands)):
            self.bands[bands[i]] = i * self.band_width

    def compact_bands(self):
        '''
            Initially each band has a fixed height,
            large enough to contain all the data points in that category.
            This function is called after all datapoints have been assigned.
            It removes vertical holes in order to compact the height of each band.
            All the data points are also repositioned.

            Note that self.bands with have a different structure on return.

            [[label, y], ...] sorted by label

            Add two artificial bands at the end:
            * one for the timeline / X Axis
            * one for the histograms
        '''
        stack = self.stack
        self.bands = sorted(
            [[label, y] for label, y in self.bands.iteritems()], key=lambda p: p[1])
        last_y = max([band[1] for band in self.bands])
        self.bands.append(['', last_y + self.band_width])  # X Axis
        self.bands.append(['', last_y + self.band_width +
                           self.band_width])  # Histograms

        offset = 0
        new_y = 0
        for band in self.bands:
            # move up all pts in this band
            y = band[1]
            offset = y - new_y
            while (y in stack):
                for point in stack[y]:
                    point[1] -= offset
                y += 1
                new_y += 1
            band[1] -= offset

            # +2 is to leave some nice space between categories on the front end
            new_y = max(new_y + 1, band[1] +
                        (self.font_size_margin / self.bar_height))

        return self.bands

    def stack_point(self, point):
        while 1:
            overlap = False
            if point[1] not in self.stack:
                self.stack[point[1]] = []
                break
            # overlap on that line?
            for pt in self.stack[point[1]]:
                if not (point[0][0] > pt[0][1] or point[0][1] < pt[0][0]):
                    # must be <> conflate group
                    if pt[5] != point[5]:
                        overlap = True
                        break
            if not overlap:
                # found a spot
                break
            # try next line
            point[1] += 1

        self.stack[point[1]].append(point)

    def reframe(self):
        '''
            Frame the drawing around the points so the first data point is
            on the left border and the last on the right border.

            Generate data for the X and Y axis.
        '''
        drawing = self.drawing
        points = self.drawing['points']

        # reframe the x values based on min date
        for point in points:
            if point[0] is not None:
                point[0][0] -= self.mins[0] or 0
                point[0][1] -= self.mins[0] or 0
        # reframe the histograms
        #self.histogram = {x - self.mins[0]: hist for x, hist in self.histogram.iteritems()}
        histogram = self.histogram
        self.histogram = {}
        for x, hist in histogram.iteritems():
            self.histogram[x - self.mins[0]] = hist

        self.histogram_height = max(
            [sum([c for c in hist.values()]) for hist in self.histogram.values()])
        for x in self.histogram.keys():
            self.histogram[x] = sorted([[comb, c] for comb, c in self.histogram[x].iteritems(
            )], key=lambda p: len(p[0]) * 10 - int(p[0][0]), reverse=True)
        drawing['histogram'] = self.histogram

        #last_y = max([point[1] for point in points])
        xaxis_y = self.bands[-2][1]

        self.context['canvas']['width'] = self.maxs[0] - self.mins[0] + 1
        self.context['canvas']['height'] = self.bands[-1][1] + \
            self.histogram_height / 2

        # X axis
        # eg. 1055, 1150 => [[5, 100, 1060], [15, 100,  1070], ...]
        step = 10
        if 1:
            # dynamic step for the labels on the X axis
            # minimum timeline width on screen (approx)
            width_timeline = 400
            # width in pixel of a x label plus some margin
            width_label = 20
            # range of x data values
            data_range = self.maxs[0] - self.mins[0]
            steps = [1, 10, 20, 50, 100, 200, 500, 1000]
            import math
            if self.fields[0]['key'] == 'locus':
                steps = [int(math.ceil(s * 2.0)) for s in steps]
            for s in steps:
                if (data_range * 1.0 / s * width_label) < width_timeline:
                    break
            step = s
        date0 = self.mins[0] - (self.mins[0] % step)

        def get_xlabel_from_xvalue(x):
            ret = '%s' % d
            if self.fields[0]['key'] == 'locus':
                ret = '%s%s' % (d / 2, 'v' if d % 2 else 'r')
            return ret

        drawing['x'] = [[d - self.mins[0], xaxis_y,
                         get_xlabel_from_xvalue(d)] for d in range(date0, self.maxs[0], step)]
        drawing['y'] = [[0, y, label, self.cat_hits.get(label, [0, 0])[
            0], self.cat_hits.get(label, [0, 0])[1]] for label, y in self.bands]

        self.add_quire_divisions()

        self.context['canvas']['drawing'] = drawing

    def add_quire_divisions(self):
        if self.fields[0]['key'] != 'locus':
            return

        drawing = self.drawing

        if not(drawing['x'] and drawing['x'][0]):
            return

        # TODO: remove hardcoded ID
        from digipal.models import ItemPart

        xaxis = drawing['x'][0][1]
        drawing['xdivs'] = []
        for quire, data in ItemPart.get_quires_from_id(1).iteritems():
            x = self.get_int_from_locus(data['start'])
            if x > self.maxs[0] or x < self.mins[0]:
                continue
            drawing['xdivs'].append([x - self.mins[0], xaxis, 'q.%s' % quire])
