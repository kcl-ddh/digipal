# -*- coding: utf-8 -*-
import re
from django import http, template
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.db.models import Q

from digipal.models import Description


@staff_member_required
@csrf_exempt
def import_view(request, app_label, model_name):
    input = request.POST.get('input_text') or ''

    import_type = None
    import_types = [
        {'label': 'Document summaries', 'key': 'hi-summaries'},
        {'label': 'Test', 'key': 'test'},
    ]
    for aimport_type in import_types:
        if request.POST.get('import_type', '') == aimport_type['key']:
            aimport_type['selected'] = 1
            import_type = aimport_type

    import_log = []

    from digipal.models import ItemPart, Source

    if import_type and import_type['key'] == 'hi-summaries':

        source_slug = 'moa'
        source = Source.objects.filter(label_slug=source_slug).first()
        if not source:
            import_log.append(
                'ERROR: could not find source "%s"' % source_slug)
        else:
            def write_data(data):
                if data:
                    # print data['ips'].count(), data['lines']
                    for ip in data['ips']:
                        written = False
                        for hi in ip.historical_items.all():
                            description, created = Description.objects.get_or_create(
                                historical_item=hi, source=source)
                            import_log.append(u'%s description for IP "%s" "%s" (#%s)' % (
                                ('created' if created else 'updated'), ip, hi.catalogue_number, ip.id))

                            description.summary = u'\n'.join(data['lines'])

                            description.save()
                            written = True

                        if not written:
                            import_log.append(
                                u'WARNING: HI missing for "%s" (#%s)' % (ip, ip.id))

                return None

            data = None
            line_number = 0
            for line in re.split(u'\n', input):
                line_number += 1
                # print line
                code = line.strip()
                if code:
                    ips = ItemPart.objects.filter(
                        current_item__shelfmark__iexact=code)
                    if not ips.count():
                        ips = ItemPart.objects.filter(
                            historical_items__catalogue_numbers__number__iexact='Document %s' % code)
                    if ips.count():
                        write_data(data)
                        # print ' => %s' % ips.count()
                        data = {'ips': ips, 'lines': []}
                    else:
                        if data:
                            data['lines'].append(code)
                        else:
                            import_log.append(
                                'WARNING: unassigned line: %s' % code)
                else:
                    data = write_data(data)

            data = write_data(data)

    context = {'input_text': input, 'import_log': '\n'.join(
        import_log), 'import_types': import_types}
    return render(request, 'admin/digipal/import.html', context)


@staff_member_required
def instances_view(request, app_label):
    context = {}
    return render(request, 'admin/digipal/instances.html', context)


@staff_member_required
def context_view(request, app_label, model_name, object_id):
    from django.contrib.contenttypes.models import ContentType

    context = {}

    # get the object
    model_class = ContentType.objects.get(
        app_label=app_label, model=model_name).model_class()
    obj = model_class.objects.get(id=object_id)

    #context['obj_tree'] = get_obj_info(obj)
    context['tree_html'] = mark_safe(get_html_from_obj_tree(get_obj_info(obj)))

    return render(request, 'admin/digipal/context.html', context)


def get_html_from_obj_tree(element):
    ret = ur''

    if element:
        for child in element['children']:
            ret += get_html_from_obj_tree(child)
        if ret:
            ret = ur'<ul>%s</ul>' % ret
        ret = ur'<li>%s%s</li>' % (element['html'], ret)

    return ret


def get_obj_info(obj, exclude_list=None):
    if exclude_list is None:
        exclude_list = {}

    ret = {
        'obj': obj,
        'type': obj._meta.object_name,
        'link': ur'/admin/%s/%s/%s/' % (obj._meta.app_label, obj._meta.model_name, obj.id),
        'children': []
    }

    info = ''

    if obj._meta.model_name == 'historicalitem':
        info_parts = []
        info = '%s, %s' % (obj.historical_item_format,
                           obj.historical_item_type)
        if info:
            info_parts = [info]
        info_parts.extend(
            ['%s' % cat_num for cat_num in obj.catalogue_numbers.all()])
        info = ', '.join(info_parts)

    if info:
        info = ur'(%s) ' % info

    exclude_list[get_obj_key(obj)] = 1

    ret['html'] = ur'<a href="%s">%s #%s: %s %s</a>[<a href="%s">edit</a>]' % (
        ret['link'] + ur'context/', ret['type'], obj.id, ret['obj'], info, ret['link'])

    for child in get_obj_children(obj):
        if get_obj_key(child) not in exclude_list:
            obj_info = get_obj_info(child, exclude_list.copy())
            ret['children'].append(obj_info)

    if ret['children']:
        ret['html'] = ur'<a class="expandable" href="#">[ - ]</a> %s' % ret['html']

    return ret


def get_obj_key(obj):
    return ur'%s-%s' % (obj._meta.object_name, obj.id)


def get_obj_children(obj):
    ret = []

    if obj._meta.model_name == 'itempart':
        ret.extend((obj.current_item,))
        ret.extend(list(obj.historical_items.all().order_by('id')))
        ret.extend(list(obj.images.all().order_by('id')))

    if obj._meta.model_name == 'currentitem':
        ret.extend(list(obj.itempart_set.all().order_by('id')))

    if obj._meta.model_name == 'historicalitem':
        ret.extend(list(obj.item_parts.all().order_by('id')))

    return ret
