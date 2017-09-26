from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Count
from mezzanine.conf import settings
import django_admin_customisations
from digipal.models import Image, HistoricalItem, Hand, Annotation
import re

#########################
#                       #
#   Utilities           #
#                       #
#########################


class RelatedObjectNumberFilter(SimpleListFilter):
    '''
        Generic Filter based on the number of related objects.
        Redefine the next 5 variables in the subclass with the relevant values.
    '''
    title = ('Number of Related Objects')
    parameter_name = ('n')

    related_table = 'digipal_image'
    foreign_key = 'item_part_id'
    this_table = 'digipal_itempart'

    this_key = 'id'

    def lookups(self, request, model_admin):
        return (
            ('0', ('0')),
            ('1', ('1')),
            ('1p', ('1+')),
            ('2p', ('2+')),
            ('3p', ('3+')),
        )

    def queryset(self, request, queryset):
        select = (ur'''((SELECT COUNT(*) FROM %s fcta WHERE fcta.%s = %s.%s) ''' %
                  (self.related_table, self.foreign_key, self.this_table, self.this_key))
        select += ur'%s )'
        if self.value() == '0':
            return queryset.extra(where=[select % ' = 0'])
        if self.value() == '1':
            return queryset.extra(where=[select % ' = 1'])
        if self.value() == '1p':
            return queryset.extra(where=[select % ' >= 1'])
        if self.value() == '2p':
            return queryset.extra(where=[select % ' > 1'])
        if self.value() == '3p':
            return queryset.extra(where=[select % ' > 2'])

#########################
#                       #
#   Custom Filters      #
#                       #
#########################


class ImageAnnotationNumber(SimpleListFilter):
    title = ('Annotations')

    parameter_name = ('Annot')

    def lookups(self, request, model_admin):
        return (
            ('1', ('At least five annotations')),
            ('2', ('Fewer than five annotations')),
            ('3', ('At least one annotation')),
            ('0', ('No annotation')),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(annotation__isnull=True)
        if self.value() == '3':
            return queryset.filter(annotation__id__gt=0).distinct()
        if self.value() == '1':
            return queryset.annotate(num_annot=Count('annotation__image__item_part')).exclude(num_annot__lt=5)
        if self.value() == '2':
            return queryset.annotate(num_annot=Count('annotation__image__item_part')).filter(num_annot__lt=5)


class ImageLocus(SimpleListFilter):
    title = 'Locus'

    parameter_name = ('locus')

    def lookups(self, request, model_admin):
        return (
            ('with', ('With locus')),
            ('without', ('Without Locus')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'with':
            return queryset.filter(locus__gt='').distinct()
        if self.value() == 'without':
            return queryset.exclude(locus__gt='').distinct()


class ImageFilterNoItemPart(SimpleListFilter):
    title = 'Item Part'

    parameter_name = ('item_part')

    def lookups(self, request, model_admin):
        return (
            ('with', ('With Item Part')),
            ('without', ('Without Item Part')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'with':
            return queryset.filter(item_part_id__gt=0).distinct()
        if self.value() == 'without':
            return queryset.filter(item_part__isnull=True).distinct()


class GraphFilterNoAnnotation(SimpleListFilter):
    title = 'Annotation'

    parameter_name = ('annotation')

    def lookups(self, request, model_admin):
        return (
            ('with', ('With annotation')),
            ('without', ('Annotation is missing')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'with':
            return queryset.filter(annotation__isnull=False).distinct()
        if self.value() == 'without':
            return queryset.filter(annotation__isnull=True).distinct()


class ImageFilterDuplicateShelfmark(SimpleListFilter):
    title = 'Duplicate Shelfmark'

    parameter_name = ('dup')

    def lookups(self, request, model_admin):
        return (
            ('1', ('has duplicate shelfmark')),
            ('-1', ('has unique shelfmark')),
        )

    def queryset(self, request, queryset):
        if self.value() in ['1', '-1']:
            all_duplicates_ids = Image.get_duplicates_from_ids().keys()

        if self.value() == '1':
            return queryset.filter(id__in=all_duplicates_ids).distinct()
        if self.value() == '-1':
            return queryset.exclude(id__in=all_duplicates_ids).distinct()


class ImageFilterDuplicateFilename(SimpleListFilter):
    title = 'Duplicate Image File'

    parameter_name = ('dupfn')

    def lookups(self, request, model_admin):
        return (
            ('1', ('has duplicate filename')),
            ('-1', ('has unique filename')),
            ('2', ('has duplicate size')),
        )

    def queryset(self, request, queryset):
        if self.value() in ['-1', '1']:
            duplicate_iipimages = Image.objects.all().values_list('iipimage').annotate(
                dcount=Count('iipimage')).filter(dcount__gt=1).values_list('iipimage', flat=True)

        if self.value() == '1':
            return queryset.filter(iipimage__in=duplicate_iipimages).distinct()
        if self.value() == '-1':
            return queryset.exclude(iipimage__in=duplicate_iipimages).distinct()
        if self.value() == '2':
            duplicate_iipimages = Image.objects.all().values_list('size').annotate(
                dcount=Count('size')).filter(dcount__gt=1).values_list('size', flat=True)
            return queryset.filter(size__in=duplicate_iipimages).distinct()


class ImageWithFeature(SimpleListFilter):
    title = ('Associated Features')

    parameter_name = ('WithFeat')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Has feature(s)')),
            ('no', ('No features')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(annotation__graph__graph_components__features__id__gt=0).distinct()
        if self.value() == 'no':
            return queryset.exclude(annotation__graph__graph_components__features__id__gt=0)


class ImageWithHand(SimpleListFilter):
    title = ('Associated Hand')

    parameter_name = ('WithHand')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Has Hand(s)')),
            ('no', ('No Hand')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(hands__id__gt=0).distinct()
        if self.value() == 'no':
            return queryset.exclude(hands__id__gt=0).distinct()


class DescriptionFilter(SimpleListFilter):
    title = ('To Fix or Check')

    parameter_name = ('toFixOrCheck')

    def lookups(self, request, model_admin):
        return (
            ('toFix', ('Needs to be fixed')),
            ('toCheck', ('Needs to be checked')),
            ('goodlikethis', ('No needs to be checked or fixed')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'toFix':
            return queryset.filter(description__contains="FIX")
        if self.value() == 'toCheck':
            return queryset.filter(description__contains="CHECK")
        if self.value() == 'goodlikethis':
            q = queryset.exclude(description__contains="CHECK")
            k = q.exclude(description__contains="FIX")
            return k


class HistoricalCatalogueNumberFilter(RelatedObjectNumberFilter):
    title = ('Number of catalogue numbers')

    parameter_name = ('ncn')

    related_table = 'digipal_cataloguenumber'
    foreign_key = 'historical_item_id'
    this_table = 'digipal_historicalitem'


class HistoricalItemDescriptionFilter(SimpleListFilter):
    title = ('To Fix or Check')

    parameter_name = ('toFixOrCheck')

    def lookups(self, request, model_admin):
        return (
            ('toFix', ('Needs to be fixed')),
            ('toCheck', ('Needs to be checked')),
            ('goodlikethis', ('No needs to be checked or fixed')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'toFix':
            return queryset.filter(description__description__contains="FIX")
        if self.value() == 'toCheck':
            return queryset.filter(description__description__contains="CHECK")
        if self.value() == 'goodlikethis':
            q = queryset.exclude(description__description__contains="CHECK")
            k = q.exclude(description__description__contains="FIX")
            return k


class ItemPartHasGroupGroupFilter(SimpleListFilter):
    title = ('Membership')

    parameter_name = ('hg')

    def lookups(self, request, model_admin):
        return (
            ('0', ('not part of a group')),
            ('1', ('part of a group')),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(group__isnull=False)
        if self.value() == '0':
            return queryset.filter(group__isnull=True)


class ItemPartHIFilter(RelatedObjectNumberFilter):
    title = ('Number of H.I.')

    parameter_name = ('hi')

    related_table = 'digipal_itempartitem'
    foreign_key = 'item_part_id'
    this_table = 'digipal_itempart'


class ItemPartMembersNumberFilter(RelatedObjectNumberFilter):
    title = ('Number of parts')

    parameter_name = ('np')

    related_table = 'digipal_itempart'
    foreign_key = 'group_id'
    this_table = 'digipal_itempart'


class ItemPartImageNumberFilter(RelatedObjectNumberFilter):
    title = ('Number of Images')

    parameter_name = ('ni')

    related_table = 'digipal_image'
    foreign_key = 'item_part_id'
    this_table = 'digipal_itempart'


class CurrentItemPartNumberFilter(RelatedObjectNumberFilter):
    title = ('Number of Parts')

    parameter_name = ('ci_nip')

    related_table = 'digipal_itempart'
    foreign_key = 'current_item_id'
    this_table = 'digipal_currentitem'


class HistoricalItemItemPartNumberFilter(RelatedObjectNumberFilter):
    title = ('Number of Parts')

    parameter_name = ('hi_nip')

    related_table = 'digipal_itempartitem'
    foreign_key = 'historical_item_id'
    this_table = 'digipal_historicalitem'


class HistoricalItemKerFilter(SimpleListFilter):
    title = ('Ker')

    parameter_name = ('ker')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Contains Ker')),
            ('no', ('Not contains Ker')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(description__description__contains="Ker")
        if self.value() == 'no':
            return queryset.exclude(description__description__contains="Ker")


class HistoricalItemGneussFilter(SimpleListFilter):
    title = ('Gneuss')

    parameter_name = ('gneuss')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Contains Gneuss Number')),
            ('no', ('Not contains Gneuss Number')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(catalogue_numbers__source__label='G.')
        if self.value() == 'no':
            return queryset.exclude(catalogue_numbers__source__label='G.')


class HandItempPartFilter(SimpleListFilter):
    title = ('numbers of ItemParts')

    parameter_name = ('morethanoneItemPart')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Has more than one Item Part')),
            ('no', ('Has not more than one Item Part')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return Hand.objects.filter(item_part__historical_items__in=HistoricalItem.objects.annotate(num_itemparts=Count('itempart')).filter(num_itemparts__gt='1'))
        if self.value() == 'no':
            return Hand.objects.filter(item_part__historical_items__in=HistoricalItem.objects.annotate(num_itemparts=Count('itempart')).exclude(num_itemparts__gt='1'))


class HandGlossNumFilter(SimpleListFilter):
    title = ('number of Glossing Hands')

    parameter_name = ('glosshandwithnum')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Has Num. Glossing hands')),
            ('no', ('Not has Num. Glossing hands')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return Hand.objects.filter(gloss_only=True).filter(num_glosses__isnull=False)
        if self.value() == 'no':
            return Hand.objects.filter(gloss_only=True).filter(num_glosses__isnull=True)


class HandGlossTextFilter(SimpleListFilter):
    title = ('has Glossing Text')

    parameter_name = ('glosshandwithtext')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Has Glossed Text')),
            ('no', ('Not has Glossed text')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return Hand.objects.filter(gloss_only=True).filter(glossed_text__isnull=False)
        if self.value() == 'no':
            return Hand.objects.filter(gloss_only=True).filter(glossed_text__isnull=True)


class HandImageNumberFilter(RelatedObjectNumberFilter):
    title = ('Number of images')

    parameter_name = ('ni')

    related_table = 'digipal_hand_images'
    foreign_key = 'hand_id'
    this_table = 'digipal_hand'


class StewartRecordFilterLegacy(admin.SimpleListFilter):
    title = 'Legacy'
    parameter_name = 'legacy'

    def lookups(self, request, model_admin):
        return (
            ('1', 'has legacy id'),
            ('0', 'no legacy id'),
        )

    def queryset(self, request, queryset):
        from django.db.models import Q
        q = Q(stokes_db__isnull=True) | Q(stokes_db__exact='')
        if self.value() == '0':
            return queryset.filter(q)
        if self.value() == '1':
            return queryset.exclude(q)


class StewartRecordFilterMerged(admin.SimpleListFilter):
    title = 'Already Merged'
    parameter_name = 'merged'

    def lookups(self, request, model_admin):
        return (
            ('1', 'yes'),
            ('0', 'no'),
        )

    def queryset(self, request, queryset):
        from django.db.models import Q
        q = Q(import_messages__isnull=True) | Q(import_messages__exact='')
        if self.value() == '0':
            return queryset.filter(q)
        if self.value() == '1':
            return queryset.exclude(q)


class RequestLogFilterEmpty(admin.SimpleListFilter):
    title = 'Result size'
    parameter_name = 'result_size'

    def lookups(self, request, model_admin):
        return (
            ('0', 'empty'),
            ('1', 'not empty'),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(result_count__gt=0).distinct()
        if self.value() == '0':
            return queryset.filter(result_count=0).distinct()


class HandFilterSurrogates(admin.SimpleListFilter):
    title = 'Surrogates'
    parameter_name = 'surrogates'

    def lookups(self, request, model_admin):
        return (
            ('1', 'with surrogates'),
            ('0', 'without surrogates'),
        )

    def queryset(self, request, queryset):
        from django.db.models import Q
        q = Q(surrogates__isnull=True) | Q(surrogates__exact='')
        if self.value() == '0':
            return queryset.filter(q)
        if self.value() == '1':
            return queryset.exclude(q)


class AnnotationFilterLinkedToText(admin.SimpleListFilter):
    title = 'Linked to text'
    parameter_name = 'linkedtext'

    def lookups(self, request, model_admin):
        return (
            ('0', 'unlinked'),
            ('1', 'linked'),
        )

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.annotate(ta=Count('textannotations'))
            if self.value() == '0':
                return queryset.filter(ta__lt=1).distinct()
            if self.value() == '1':
                return queryset.exclude(ta__lt=1).distinct()


class AnnotationFilterDuplicateClientid(admin.SimpleListFilter):
    title = 'Duplicate clientid'
    parameter_name = 'dupclid'

    def lookups(self, request, model_admin):
        return (
            ('0', 'unique'),
            ('1', 'duplicate'),
        )

    def queryset(self, request, queryset):
        if self.value():
            '''
            select clientid
            from digipal_annotation an
            where length(clientid) > 0
            group by clientid
            having count(*) > 1
            ;
            '''

            dupe_geo = Annotation.objects.filter(
                clientid__isnull=False
            ).values_list(
                'clientid', flat=True
            ).annotate(
                count_geo=Count('id')
            ).order_by(
                'clientid'
            ).filter(
                count_geo__gt=1
            ).distinct()

            dupe_geo = list(dupe_geo)

            if self.value() == '1':
                return queryset.filter(clientid__in=dupe_geo).distinct()
            if self.value() == '0':
                return queryset.exclude(clientid__in=dupe_geo).distinct()
