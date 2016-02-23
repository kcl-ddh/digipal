def draw_overview(faceted_search, context, request):
    view = Overview(faceted_search, context, request)
    view.draw()

class Overview(object):
    '''
        IN
            faceted_search
            context
            request

        OUT
            Visualisation as a TIMELINE
            Where result is encoded as a DATA POINT and represented by a BAR
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
                width
                height
                drawing
                    points:
                        [
                            [[x1, x2], y, id, label, group0]
                            ...
                        ]
                    point_height: 7
                    x:
                        # x, y, label
                        [[0, 2000, '1000', 10, 2000, '1010', ...]]
                    y:
                        # x, y, label
                        []
    '''

    def __init__(self, faceted_search, context, request):
        # if True, we group all the results by document to avoid stacking graphs or clauses
        self.conflate = 1
        self.faceted_search = faceted_search
        self.context = context
        self.request = request
        # an index used to detect data point overlap and create stack
        # [y][[x0, x1], [x0, x1]]
        self.stack = {}

        self.cat_hits = {}

        self.mins = [None, None]
        self.maxs = [None, None]

    def draw(self):
        if self.faceted_search.get_selected_view()['key'] != 'overview': return

        self.set_fields()

        self.draw_internal()

        self.compact_bands()

        self.reframe()

    def draw_internal(self):
        faceted_search = self.faceted_search
        context = self.context
        request = self.request

        self.context['canvas'] = {'width': 500, 'height': 500}

        self.drawing = {'points': [], 'x': [], 'y': [], 'point_height': 7}

        points = self.drawing['points']

        # {'agreement': [10, 20]}

        print 'OVERVIEW SCAN'

        records = context['result']

        self.init_bands()

        from digipal.utils import get_range_from_date, MAX_DATE_RANGE

        # process all records
        for record in records:
            found = 1 if getattr(record, 'found', 0) else 0

            # TODO: one request for the whole thing
            values = []
            for field in self.fields:
                values.append(faceted_search.get_record_field(record, field))

            x = values[0]
            ys = values[1]
            conflateid = values[2]

            # convert x to numerical value
            if self.fields[0]['type'] == 'date':
    #             if found:
    #                 print x, get_midpoint_from_date_range(x)
                #x = get_midpoint_from_date_range(x)
                x = get_range_from_date(x)
            else:
                # ()TODO: other type than date for x
                x = 0

            # turn all x into range
            if not isinstance(x, list):
                x = [x, x]

            # update the min / max x
            if x[0] is not None and x[0] not in MAX_DATE_RANGE and (self.mins[0] is None or self.mins[0] > x[0]):
                self.mins[0] = x[0]
            if x[1] is not None and x[1] not in MAX_DATE_RANGE and (self.maxs[0] is None or self.maxs[0] < x[1]):
                self.maxs[0] = x[1]

            # convert y to numerical value
            if not isinstance(ys, list):
                ys = [ys]
            for v in ys:
                y = self.bands.get(v, 0)

                # add the points
                label = faceted_search.get_record_label_html(record, request);
                point = [x, y, found, label, record.get_absolute_url(), conflateid]

                self.stack_point(point)
                points.append(point)

                # increment hits per category
                self.cat_hits[v] = self.cat_hits.get(v, [0, 0][:])
                self.cat_hits[v][0] += 1
                if found:
                    self.cat_hits[v][1] += 1

    def set_fields(self):
        '''
            set self.fields = array of faceted fields such that:
                self.fields[0] = field for Y dimensions (e.g. { hi_date })
                self.fields[1] = field for bands (e.g. { hi_date } )
                self.fields[2] = field for conflating (e.g. { ip.id } )
        '''
        faceted_search = self.faceted_search
        context = self.context

        #fields = ['hi_date', 'medieval_archive']
        #fields = ['hi_date', 'clause_type']
        category_field = faceted_search.get_field_by_key(self.request.REQUEST.get('vcat', 'hi_type'))
        if category_field is None: category_field = faceted_search.get_field_by_key('hi_type')
        context['vcat'] = category_field

        context['vcats'] = [field for field in faceted_search.get_fields() if field.get('vcat', True)]

        fields = ['hi_date', category_field['key'], 'CONFLATEID' if self.conflate else 'url']
        self.fields = map(lambda field: faceted_search.get_field_by_key(field), fields)

    def reframe(self):

        drawing = self.drawing
        points = self.drawing['points']

        # reframe the x values based on min date
        for point in points:
            if point[0] is not None:
                point[0][0] -= self.mins[0]
                point[0][1] -= self.mins[0]

        last_y = max([point[1] for point in points])

        self.context['canvas']['width'] = self.maxs[0] - self.mins[0] + 1
        self.context['canvas']['height'] = last_y

        # X axis
        # eg. 1055, 1150 => [[5, 100, 1060], [15, 100,  1070], ...]
        step = 10
        date0 = self.mins[0] - (self.mins[0] % step)
        drawing['x'] = [[d - self.mins[0], last_y + 2, '%s' % d] for d in range(date0, self.maxs[0], step)]
        drawing['y'] = [[0, y, label, self.cat_hits.get(label, [0, 0])[0], self.cat_hits.get(label, [0, 0])[1]] for label, y in self.bands]

        self.context['canvas']['drawing'] = drawing

    def init_bands(self):
        '''
            set self.bands = {'agreement': 0, 'brieve': 1000, LABEL: TOPY}
        '''
        # determine large y bands for the categories
        band_width = 5000
        # eg. ['type1', 'type2']
        from digipal.utils import sorted_natural
        l = []
        for record in self.context['result']:
            v = self.faceted_search.get_record_field(record, self.fields[1])
            if isinstance(v, list):
                # flatten it, it may contain nested lists
                l.extend(v)
            else:
                l.append(v)

        self.bands = sorted_natural(list(set(l)))
        # eg. {'type1': 0, 'type2': 1000}
        self.bands = {self.bands[i]: i*band_width for i in range(0, len(self.bands))}

    def compact_bands(self, min_height=14):
        stack = self.stack
        self.bands = sorted([[label, y] for label, y in self.bands.iteritems()], key=lambda p: p[1])
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
            # +10 is to leav enough space to write the label for the category
            # Note that 10 is scaled so difficult found it by trial and errors
            new_y = max(new_y + 2, band[1] + (min_height / self.drawing['point_height'] + 1))

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
