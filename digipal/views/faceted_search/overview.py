def draw_overview(faceted_search, context, request):
    if faceted_search.get_selected_view()['key'] != 'overview': return

    context['canvas'] = {'width': 500, 'height': 500}

    drawing = {'points': [], 'x': [], 'y': []}
    '''
        points:
            [[x1, x2], y, id, label, group0]
        x:
            [[0, '1000', 10: '1010', ...]]
        y:
    '''

    points = drawing['points']

    from digipal.utils import get_midpoint_from_date_range, get_range_from_date

    print 'OVERVIEW SCAN'
    #fields = ['hi_date', 'medieval_archive']
    #fields = ['hi_date', 'clause_type']
    category_field = faceted_search.get_field_by_key(request.REQUEST.get('vcat', 'hi_type'))
    context['vcat'] = category_field

    context['vcats'] = [field for field in faceted_search.get_fields() if field.get('vcat', True)]

    fields = ['hi_date', category_field['key']]
    fields = map(lambda field: faceted_search.get_field_by_key(field), fields)
    mins = [None, None]
    maxs = [None, None]

    records = context['result']

    # determine large y bands for the categories
    band_width = 10
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

        # convert x to numerical value
        if fields[0]['type'] == 'date':
            if found:
                print x, get_midpoint_from_date_range(x)
            x = get_midpoint_from_date_range(x)
            #x = get_range_from_date(x)
        else:
            # ()TODO: other type than date for x
            x = 0

        if x is not None:
            if mins[0] is None or mins[0] > x:
                mins[0] = x
            if maxs[0] is None or maxs[0] < x:
                maxs[0] = x

        # convert y to numerical value
        if not isinstance(ys, list):
            ys = [ys]
        for v in ys:
            y = bands.get(v, 0)

            # add the points
            point = [x, y, found]
            points.append(point)

            # increment hits per category
            cat_hits[v] = cat_hits.get(v, [0, 0][:])
            cat_hits[v][0] += 1
            if found:
                cat_hits[v][1] += 1

    # reframe the x values based on min
    for point in points:
        if point[0] is not None:
            point[0] -= mins[0]

    last_y = max([point[1] for point in points])

    context['canvas']['width'] = maxs[0] - mins[0] + 1
    context['canvas']['height'] = last_y

    # X axis
    # eg. 1055, 1150 => [[5, 100, 1060], [15, 100,  1070], ...]
    step = 10
    date0 = mins[0] - (mins[0] % step)
    drawing['x'] = [[d - mins[0], last_y + 2, '%s' % d] for d in range(date0, maxs[0], step)]
    drawing['y'] = [[0, y, label, cat_hits.get(label, [0, 0])[0], cat_hits.get(label, [0, 0])[1]]  for label, y in bands.iteritems()]

    context['canvas']['drawing'] = drawing
