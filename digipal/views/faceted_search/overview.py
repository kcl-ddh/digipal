def draw_overview(faceted_search, context, request):
    view = Overview(faceted_search, context, request)
    view.draw()

class Overview(object):
    def __init__(self, faceted_search, context, request):
        # if True, we group all the results by document to avoid stacking graphs or clauses
        self.collapse = 1
        self.faceted_search = faceted_search
        self.context = context
        self.request = request
        # an index used to detect data point overlap and create stack
        # [y][[x0, x1], [x0, x1]]
        self.stack = {}

    def draw(self):
        faceted_search = self.faceted_search
        context = self.context
        request = self.request

        if faceted_search.get_selected_view()['key'] != 'overview': return

        self.context['canvas'] = {'width': 500, 'height': 500}

        drawing = {'points': [], 'x': [], 'y': [], 'point_height': 7}
        '''
            points:
                [[x1, x2], y, id, label, group0]
            x:
                [[0, '1000', 10: '1010', ...]]
            y:
        '''

        points = drawing['points']

        from digipal.utils import get_midpoint_from_date_range, get_range_from_date, MAX_DATE_RANGE

        print 'OVERVIEW SCAN'
        #fields = ['hi_date', 'medieval_archive']
        #fields = ['hi_date', 'clause_type']
        category_field = faceted_search.get_field_by_key(self.request.REQUEST.get('vcat', 'hi_type'))
        if category_field is None: category_field = faceted_search.get_field_by_key('hi_type')
        context['vcat'] = category_field

        context['vcats'] = [field for field in faceted_search.get_fields() if field.get('vcat', True)]

        fields = ['hi_date', category_field['key'], 'COLLAPSEID' if self.collapse else 'url']
        fields = map(lambda field: faceted_search.get_field_by_key(field), fields)
        mins = [None, None]
        maxs = [None, None]

        records = context['result']

        # determine large y bands for the categories
        band_width = 1000
        # eg. ['type1', 'type2']
        from digipal.utils import sorted_natural
        l = []
        for record in records:
            v = faceted_search.get_record_field(record, fields[1])
            if isinstance(v, list):
                # flatten it, it may contain nested lists
                l.extend(v)
            else:
                l.append(v)

        bands = sorted_natural(list(set(l)))
        # eg. {'type1': 0, 'type2': 1000}
        bands = {bands[i]: i*band_width for i in range(0, len(bands))}

        # {'agreement': [10, 20]}
        cat_hits = {}


        # process all records
        for record in records:
            found = 1 if getattr(record, 'found', 0) else 0

            # TODO: one request for the whole thing
            values = []
            for field in fields:
                values.append(faceted_search.get_record_field(record, field))

            x = values[0]
            ys = values[1]
            collapseid = values[2]

            # convert x to numerical value
            if fields[0]['type'] == 'date':
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
            if x[0] is not None and x[0] not in MAX_DATE_RANGE and (mins[0] is None or mins[0] > x[0]):
                mins[0] = x[0]
            if x[1] is not None and x[1] not in MAX_DATE_RANGE and (maxs[0] is None or maxs[0] < x[1]):
                maxs[0] = x[1]

            # convert y to numerical value
            if not isinstance(ys, list):
                ys = [ys]
            for v in ys:
                y = bands.get(v, 0)

                # add the points
                label = faceted_search.get_record_label_html(record, request);
                point = [x, y, found, label, record.get_absolute_url(), collapseid]

                self.stack_point(point)
                points.append(point)

                # increment hits per category
                cat_hits[v] = cat_hits.get(v, [0, 0][:])
                cat_hits[v][0] += 1
                if found:
                    cat_hits[v][1] += 1

        # reframe the x values based on min
        print mins, maxs
        for point in points:
            if point[0] is not None:
                point[0][0] -= mins[0]
                point[0][1] -= mins[0]

        # remove holes in bands
        bands = self.compact_bands(self.stack, drawing, bands)

        last_y = max([point[1] for point in points])

        context['canvas']['width'] = maxs[0] - mins[0] + 1
        context['canvas']['height'] = last_y

        # X axis
        # eg. 1055, 1150 => [[5, 100, 1060], [15, 100,  1070], ...]
        step = 10
        date0 = mins[0] - (mins[0] % step)
        drawing['x'] = [[d - mins[0], last_y + 2, '%s' % d] for d in range(date0, maxs[0], step)]
        drawing['y'] = [[0, y, label, cat_hits.get(label, [0, 0])[0], cat_hits.get(label, [0, 0])[1]] for label, y in bands]

        context['canvas']['drawing'] = drawing

    def compact_bands(self, stack, drawing, bands, min_height=14):
        bands = sorted([[label, y] for label, y in bands.iteritems()], key=lambda p: p[1])
        offset = 0
        new_y = 0
        for band in bands:
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
            new_y = max(new_y + 2, band[1] + (min_height / drawing['point_height'] + 1))

        return bands

    def stack_point(self, point):
        while 1:
            overlap = False
            if point[1] not in self.stack:
                self.stack[point[1]] = []
                break
            # overlap on that line?
            for pt in self.stack[point[1]]:
                if not (point[0][0] > pt[0][1] or point[0][1] < pt[0][0]):
                    # must be <> collapsing group
                    if pt[5] != point[5]:
                        overlap = True
                        break
            if not overlap:
                # found a spot
                break
            # try next line
            point[1] += 1

        self.stack[point[1]].append(point)
