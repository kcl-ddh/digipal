# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from mezzanine.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option
import utils
from digipal.models import Text, CatalogueNumber, Description, TextItemPart, Collation
from digipal.models import Text
from digipal.models import HistoricalItem, ItemPart
from django.db.models import Q
from digipal.models import *


class Command(BaseCommand):
    help = """
Digipal database management tools.

Commands:

  backup [--table TABLE_NAME] [BACKUP_NAME]
                        Backup a database into a file.

  restore BACKUP_NAME
                        Restores a database from a backup.

  list
                        Lists backup files.

  tables [--db=DATABASE_ALIAS] [--table TABLE_NAME] [--order=[-]c|d|n]
                        Lists the tables in the database, their size and most recent change
                        Use --table PATTERN to select which table to display

  fixseq
                        Fix the postgresql sequences.
                        Useful when you get a duplicate key violation on insert after restoring a database.

  tidyup1 [--db=DATABASE_ALIAS]
                        Tidy up the data in the digipal tables (See Mantis issue #5532)
                        Refresh all the display_labels fields.

  checkdata1
                        Check for issues in the data (See Mantis issue #5532)

  cleanlocus ITEMPARTID1 [ITEMPARTID2 ...] [--force]
                        Remove the v/r from the Image.locus field.
                        For all pages where Image.item_part_id in (ITEMPARTID1 ITEMPARTID2 ...).
                        Use --force to also change Image.item_part.pagination to true.
                        Use checkdata1 to list the id of the pages and item_parts records.

  drop_tables [--db=DATABASE_ALIAS] [--table TABLE_NAME]

  pseudo_items
                         Convert Sawyer pseudo-items into Text records

  duplicate_cis
                         Returns duplicate CIs

  add_cartulary_his
                          Create missing cartulary HIs from the SS HIs

  merge_rf
                          Merge Reconstructed Folios (ScandiPal)

  merge_frg
                          Merge Fragments (ScandiPal)

  version
                          show the version of the digipal code

  build
                          show the build number and the build date from the database

  setbuild [--branch=master|staging]]
                          set the build number and the build date in the database

  create_index table col1,col2,col3
                          create indexes
    """

    args = 'backup|restore|list|tables|fixseq|tidyup1|checkdata1|pseudo_items|duplicate_ips'
    #help = 'Manage the Digipal database'
    option_list = BaseCommand.option_list + (
        make_option('--db',
                    action='store',
                    dest='db',
                    default='default',
                    help='Database alias'),
        make_option('--branch',
                    action='store',
                    dest='branch',
                    default='',
                    help='Branch name'),
        make_option('--force',
                    action='store_true',
                    dest='force',
                    default=False,
                    help='Force changes despite warnings'),
        make_option('--table',
                    action='store',
                    dest='table',
                    default='',
                    help='Name of the table to backup'),
        make_option('--order',
                    action='store',
                    dest='order',
                    default='',
                    help='Sort order'),
        make_option('--dry-run',
                    action='store_true',
                    dest='dry-run',
                    default=False,
                    help='Dry run, don\'t change any data.'),
    )

    def show_version(self):
        import digipal
        print 'DigiPal version %s' % digipal.__version__

    def merge_frg(self):
        '''
        * Merge the Fragments
        '''
        from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
        con = connections['default']
        con.enter_transaction_management()
        con.managed()

        # Find all the couple of fragment where the SHelfmark + locus only vary
        # on the side info
        fragments = {}
        for fragment in ItemPart.objects.filter(type=1).order_by('id'):
            # print (ur'Fragment #%d %s' % (fragment.id,
            # fragment)).encode('ascii', 'ignore')
            key = '%s, %s' % (fragment.current_item.shelfmark, fragment.locus)
            key = re.sub(ur'\W+', '', key.lower())
            val = fragments.get(key, [])
            if not val:
                fragments[key] = val
            val.append(fragment)

        for key, val in fragments.iteritems():
            fragment = val[0]
            if len(val) > 1:
                print 'WARNING: fragments with the same shelfmark + locus: %s %s' % (key, ', '.join(['#%s' % fragment.id for fragment in val]))
                continue
            if key.endswith('verso'):
                # search for the recto to merge into
                keyr = key[0:-5] + 'recto'
                fragmentr = fragments.get(keyr, [None])[0]
                if not fragmentr:
                    print 'WARNING: no recto found %s %s' % (fragment.id, keyr)
                else:
                    self.merge_frg_verso_into_recto(fragment, fragmentr)

        # Make sure they belong to the same group
        if self.is_dry_run():
            con.rollback()
            print 'Nothing actually written (remove --dry-run option for permanent changes).'
        else:
            con.commit()
        con.leave_transaction_management()

    def merge_frg_verso_into_recto(self, fv, fr):
        print ('Merge pair %s: #%s (verso) -> #%s (recto)' %
               (fv.display_label, fv.id, fr.id)).encode('ascii', 'ignore')

        # last checks
        if fv.group != fr.group:
            print '\tWARNING: the pair of fragments belong to different groups.'
            if fr.group:
                print '\t\t#%s %s' % (fr.group.id, fr.group)
            if fv.group:
                print '\t\t#%s %s' % (fv.group.id, fv.group)
            return

        # Check that the f's HI = group HI
        for f in [fv, fr]:
            if f.group and f.group.historical_item != f.historical_item:
                print '\tWARNING: Fragment #%s has different HI than group.' % f.id
                return

        # now it's safe to merge

        # remove side info from merged fragment
        fr.locus = re.sub(ur'\s*,?\s*recto\s*$', ur'', fr.locus)
        fr.group_locus = ''
        fr.save()

        # reconnect images
        for image in fr.images.all():
            if image.locus and image.locus.strip():
                print '\tWARNING: image has locus: #%s "%s"' % (image.id, image.locus)
            else:
                image.locus = 'recto'
            image.save()
            print '\t\tImage #%d (recto) : %s' % (image.id, image.custom_label)

        for image in fv.images.all():
            if image.locus and image.locus.strip():
                print '\tWARNING: image has locus: #%s "%s"' % (image.id, image.locus)
            else:
                image.locus = 'verso'
            image.item_part = fr
            image.save()
            print '\t\tImage #%d (verso) : %s' % (image.id, image.custom_label)

        # merge/reconnect the hands
        for handv in fv.hands.all():
            handr = fr.hands.filter(label=handv.label)
            if handr.count():
                handr = handr[0]
                print '\t\tHands to merge : #%d %s (verso) -> #%d %s (recto)' % (handv.id, handv, handr.id, handr)
                # reconnect to images from handv to handr
                for image in handv.images.all():
                    print '\t\t\tConnect recto hand #%d to image #%d' % (handr.id, image.id)
                    handr.images.add(image)
                    handr.save()
                # reconnect the graphs to the recto hand
                for graph in handv.graphs.all():
                    print '\t\t\tConnect verso graph #%d to recto hand #%d' % (graph.id, handr.id)
                    graph.hand = handr
                    graph.save()
                handv.delete()
            else:
                print '\t\tHand to reconnect: #%d %s' % (handv.id, handv)
                handv.item_part = fr
                handv.save()

        # delete the verso
        fv.delete()

    def merge_rf(self):
        '''
        * Merge the RF
        * Make sure display label = HI + locus
        * Add a new field to the Image: custom_label
            * On save display_label = custom_label if not blank
            * Show the display_label and custom_label in the admin
        * Find all the RF with a r and v
            * Remove CI from RF
            * Reconnect RFv to RFr?
                * Reconnect Image from RFv to RFr
                * Set Image.locus = 'recto'/'verso'
                * Set Image.custom_label = IP display label
            * Remove RFv
            * Remove 'recto' from RFr

        IP #231
         '''
        from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
        con = connections['default']
        con.enter_transaction_management()
        con.managed()

        rf_type = ItemPartType.objects.get(name='Reconstructed Folio')
        rfs_merged = []
        for hi in HistoricalItem.objects.all():
            print 'HI #%s, %s' % (hi.id, hi)

            # get the reconstructed folios
            rfs = hi.item_parts.filter(type=rf_type)

            for rf in rfs:
                if rf.locus and re.search(ur'(?i)verso', rf.locus):
                    # we got a verso, find the corresponding recto
                    for rf2 in rfs:
                        if (rf2.current_item == rf.current_item) and \
                                re.sub(ur'\s', '', rf2.locus.lower()) == re.sub(ur'\s', '', rf.locus.lower().replace('verso', 'recto')):
                            self.merge_rf_verso_into_recto(rf, rf2)
                            rfs_merged.append(rf2)
                            break

        # RFr.group_id = RFv.id and vice versa! After merging it becomes RF.group_id = RF.id
        # We remove this
        for ip in ItemPart.objects.all().order_by('id'):
            if ip.group and ip.group.id == ip.id:
                print 'Remove self-grouping, Item Part #%d cannot be its own group' % id
                ip.group = None
                ip.group_locus = None
                ip.save()

        # remove the reference to the CI if it already exists in one of the
        # fragments
        rfs = ItemPart.objects.filter(type=rf_type).order_by('id')
        for rf in rfs:
            if rf.current_item and ItemPart.objects.filter(group=rf, current_item=rf.current_item).count():
                print '\tREMOVE CI (IP #%s, %s)' % (rf.id, rf)
                rf.current_item = None
            else:
                pass
                print '\tLEAVE IP #%d %s' % (rf.id, rf)
            if not rf.current_item:
                rf.locus = None
            rf.save()

        if self.is_dry_run():
            con.rollback()
            print 'Nothing actually written (remove --dry-run option for permanent changes).'
        else:
            con.commit()
        con.leave_transaction_management()

    def merge_rf_verso_into_recto(self, rfv, rfr):
        print '\tMerge RF #%s into RF #%s' % (rfv.id, rfr.id)
        # merge verso into recto
        rf_type = ItemPartType.objects.get(name='Reconstructed Folio')

        if rfr.group and rfr.group.id == rfv.id:
            rfr.group = None
            rfr.group_locus = None
            rfr.save()

        # reconnect images
        for image in rfr.images.all():
            image.custom_label = image.display_label
            image.locus = 'recto'
            image.save()
            print '\t\tImage %d (recto) : %s' % (image.id, image.custom_label)

        for image in rfv.images.all():
            image.custom_label = image.display_label
            image.item_part = rfr
            image.locus = 'verso'
            image.save()
            print '\t\tImage %d (verso) : %s' % (image.id, image.custom_label)

        # reconnect parts/fragments
        for fragment in rfr.subdivisions.exclude(type=rf_type):
            fragment.group_locus = 'recto'
            fragment.save()
            print '\t\tFragment %d (recto) : %s' % (fragment.id, fragment.display_label)

        for fragment in rfv.subdivisions.exclude(type=rf_type):
            fragment.group = rfr
            fragment.group_locus = 'verso'
            fragment.save()
            print '\t\tFragment %d (verso) : %s' % (fragment.id, fragment.display_label)

        # merge/reconnect the hands
        for handv in rfv.hands.all():
            handr = rfr.hands.filter(label=handv.label)
            if handr.count():
                handr = handr[0]
                print '\t\tHands to merge : #%d %s (verso) -> #%d %s (recto)' % (handv.id, handv, handr.id, handr)
                # reconnect to images from handv to handr
                for image in handv.images.all():
                    print '\t\t\tConnect recto hand #%d to image #%d' % (handr.id, image.id)
                    handr.images.add(image)
                    handr.save()
                # reconnect the graphs to the recto hand
                for graph in handv.graphs.all():
                    print '\t\t\tConnect verso graph #%d to recto hand #%d' % (graph.id, handr.id)
                    graph.hand = handr
                    graph.save()
                handv.delete()
            else:
                print '\t\tHand to reconnect: #%d %s' % (handv.id, handv)
                handv.item_part = rfr
                handv.save()

        # delete verso
        rfv.group = None
        rfv.delete()

    @transaction.atomic
    def dropTables(self, options):
        from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
        con = connections[options.get('db')]
        table_filter = options.get('table', '')
        if not table_filter:
            raise CommandError(
                'Please provide a table filter using the --table option.')
        if table_filter == 'ALL':
            table_filter = ''

        tables = con.introspection.table_names()
        tables.sort()

        # con.enter_transaction_management()
        # con.managed()
        # con.disable_constraint_checking()

        c = 0
        for table in tables:
            if re.search(r'%s' % table_filter, table):
                print 'DROP %s' % table
                utils.dropTable(con, table, self.is_dry_run())
                c += 1

        # con.commit()
        # con.leave_transaction_management()

        print '\n%s tables' % c

    def showTables(self, options):
        from django.db import connections

        table_filter = options.get('table', '')
        order = options.get('order', '')
        if not order:
            order = 'n'

        if table_filter == 'ALL':
            table_filter = ''

        con = connections[options.get('db')]

        # 1. find all the remote tables starting with the prefix
        tables = con.introspection.table_names()
        tables.sort()

        cursor = con.cursor()

        date_fields = ['last_login', 'modified', 'publish_date',
                       'submit_date', 'action_time', 'entry_time', 'applied']

        table_displays = {}

        from datetime import datetime

        from digipal.utils import ProgressBar

        pbar = ProgressBar(len(tables))

        c = 0
        tc = 0
        table_info = []
        for table in tables:
            tc += 1
            pbar.update(tc)
            if re.search(r'%s' % table_filter, table):
                c += 1
                count = utils.sqlSelectCount(con, table)
                # find datetime field
                table_desc = con.introspection.get_table_description(
                    cursor, table)
                max_date = ''
                table_key = ''
                for field in table_desc:
                    #field_type = con.introspection.data_types_reverse.get(field[1], '')
                    # if re.search('(?i)datetime', field_type):
                    #    print field[0]
                    field_name = field[0]
                    if field_name in date_fields:
                        max_date = utils.sqlSelectMaxDate(
                            con, table, field_name)
                        if max_date and isinstance(max_date, datetime):
                            table_key = max_date.strftime("%Y%m%d%H%M%S")
                            max_date = max_date.strftime("%y-%m-%d %H:%M:%S")
                        else:
                            max_date = ''

                        # print '%s = %s' % (field_name, max_date)
                #table_display = '%10s%20s %s' % (count, max_date, table)
                table_info.append([count, max_date, table])
                # print table_display

#                 if table_key:
#                     table_displays[table_key] = table_display

        pbar.complete()

        reverse = ('-' in order)
        key_index = 2
        if 'c' in order:
            key_index = 0
        if 'd' in order:
            key_index = 1

        table_info = sorted(
            table_info, key=lambda t: t[key_index], reverse=reverse)

        print '%10s%20s %s' % ('Count', 'Date', 'Name')
        for table in table_info:
            table_display = '%10s%20s %s' % (table[0], table[1], table[2])
            print table_display

        print '\n%s tables' % c

        cursor.close()

    def checkData1(self, options):
        print 'Checkup after tidy up operations (See Mantis issue #5532)'

        # ----------------------------------------------

        print 'A. Remove \'f\' and \'r\' from Image.locus when image.item_part.pagination = true.'
        print 'To remove the f/v from the Image.locus, try python manage.py dpdb cleanlocus ITEMPARTID1 ITEMPARTID2 ...'

        print
        from digipal.models import Image
        from django.db.models import Q
        images = Image.objects.filter((Q(locus__endswith=r'v') | Q(
            locus__endswith=r'r')), item_part__pagination=True).order_by('item_part', 'id')
        if not images:
            print 'No problem found.'
        for image in images:
            if image.item_part:
                item_part_name = '[Encoding error]'
                try:
                    item_part_name = u'%s' % image.item_part
                    item_part_name = item_part_name.encode(
                        'ascii', 'xmlcharrefreplace')
                except:
                    pass
                print 'Image# %-5s: %-8s (ItemPart #%s: %s)' % (image.id, image.locus.encode('ascii', 'xmlcharrefreplace'), image.item_part.id, item_part_name)

        # ----------------------------------------------

        print '3. Detect unnecessary commas from display labels (HistoricalItem, Scribe, ItemPart, Allograph and derived models)'

        import digipal.models
        model_class_names = [c for c in dir(
            digipal.models) if re.search('^[A-Z]', c)]

        c = 0
        for model_class_name in model_class_names:
            c += 1
            model_class = getattr(digipal.models, model_class_name)
            models = model_class.objects.all().order_by('id')
            print '\t(%d / %d, %d records)\t%s' % (c, len(model_class_names), len(models), model_class._meta.object_name)
            for model in models:
                try:
                    name = u'%s' % model
                    if re.search(ur'(;\s*$)|(;\s*;)', name):
                        print u'%d %s' % (model.id, model)
                    if re.search(ur'(:\s*$)|(:\s*:)', name):
                        print u'%d %s' % (model.id, model)
                    if re.search(ur'(,\s*$)|(,\s*,)', name):
                        print u'%d %s' % (model.id, model)
                    if re.search('(\.\s*\.)', name):
                        print u'%d %s' % (model.id, model)
                except:
                    # encoding error, ignore for now
                    continue

    def cleanlocus(self, item_partids, options):
        if len(item_partids) < 1:
            raise CommandError(
                'Please provide a list of item part IDs. e.g. dpdb cleanlocus 10 30')
        from digipal.models import Image
        images = Image.objects.filter(
            item_part__in=item_partids).order_by('id')
        c = 0
        for image in images:
            image.locus = re.sub(ur'(.*)(r|v)$', ur'\1', image.locus)
            print 'Image #%s, locus = %s' % (image.id, image.locus.encode('ascii', 'xmlcharrefreplace'))
            if not image.item_part.pagination:
                if options.get('force', False):
                    image.item_part.pagination = True
                    image.item_part.save()
                    print 'WARNING: forced image.item_part.pagination = true (item part %s)' % image.item_part.id
                else:
                    print 'WARNING: Not saved as image.item_part.pagination = false (item part %s)' % image.item_part.id
                continue
            image.save()
            c += 1
        print '%s loci modified.' % c

    def tidyUp1(self, options):
        print 'Tidy up operations (See Mantis issue #5532)'

        print 'C. Import Evidence and Reference fields from legacy database.'

        from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
        con = connections['legacy']
        con_dst = connections[options.get('db', 'default')]
        con_dst.enter_transaction_management()
        con_dst.managed()
        con_dst.disable_constraint_checking()

        tables = con.introspection.table_names()
        tables.sort()

        cursor = con.cursor()
        cursor_dst = con_dst.cursor()

        migrate_fields = ['evidence', 'reference']
        table_mapping = {
            # ref is a char (folio number)
            'charters':         'digipal_historicalitem',
            # reference is a FK to reference, evidence char(128)
            'date evidence':     'digipal_dateevidence',
            'facsimiles':         '',  # ??? no table in dst
            'ms dates':         'digipal_date',  # evidence char
            'ms origins':         'digipal_itemorigin',  # evidence char
            'ms owners':         'digipal_owner',  # evidence char
            'place evidence':     'digipal_placeevidence',  # ref FK, evidence char
            'references':         '',  # 'digipal_reference', already imported
            'scribes':             'digipal_scribe',  # ref char => legacy_reference
        }

        # NEW_DIGIPAL_REFERENCE_ID = reference_mapping[LEGACY_REFERENCE_ID]
        reference_mapping = {}
        cur_dst = utils.sqlSelect(
            con_dst, 'select id, legacy_id from digipal_reference where legacy_id > 0')
        for ref in cur_dst.fetchall():
            reference_mapping[ref[1]] = ref[0]
        cur_dst.close()

        for table in tables:
            table_desc = con.introspection.get_table_description(cursor, table)
            for field in table_desc:
                #field_type = con.introspection.data_types_reverse.get(field[1], '')
                # if re.search('(?i)datetime', field_type):
                #    print field[0]
                field_name = field[0]
                if re.search('(?i)(reference|evidence)', field_name):
                    print 'LEGACY.%s.%s' % (table, field_name)
                    table_dst = table_mapping.get(table, '')
                    if not table_dst:
                        print 'WARNING: not mapping found in new Digipal database.'
                        continue

                    field_name_dst = field_name.lower()

                    table_dest_desc = con_dst.introspection.get_table_description(
                        cursor_dst, table_dst)
                    table_dest_field_names = [f[0] for f in table_dest_desc]

                    if field_name_dst == 'reference':
                        if 'legacy_reference' in table_dest_field_names:
                            field_name_dst = 'legacy_reference'
                        if 'reference_id' in table_dest_field_names:
                            field_name_dst = 'reference_id'

                    if field_name_dst not in table_dest_field_names:
                        print 'WARNING: target field not found (%s.%s)' % (table_dst, field_name_dst)

                    print '\tcopy to %s.%s' % (table_dst, field_name_dst)

                    # scan all the legacy records
                    cur_src = utils.sqlSelect(
                        con, 'select id, `%s` from `%s` order by id' % (field_name, table))
                    recs_src = cur_src.fetchall()

                    missing = 0
                    written = 0

                    if recs_src:
                        select = 'select id, legacy_id, %s from %s where legacy_id > 0'
                        if table_dst == 'digipal_historicalitem':
                            select += ' and historical_item_type_id = 1'
                        cur_dst = utils.sqlSelect(
                            con_dst, select % (field_name_dst, table_dst))
                        recs_dst = {}
                        for rec_dst in cur_dst.fetchall():
                            if rec_dst[1] in recs_dst:
                                print 'More than one record with the same legacy_id %s %s' % (rec_dst[1], table_dst)
                                exit()
                            recs_dst[rec_dst[1]] = rec_dst

                        if not recs_dst:
                            print '\tWARNING: target table has no legacy records'
                            continue

                        for rec in recs_src:
                            if rec[0] not in recs_dst:
                                #'print '\tWARNING: records is missing (legacy_id #%s)' % rec[0]
                                missing += 1
                                continue
                            (rec_dst_id, rec_dst_legacy_id,
                             rec_dst_value) = recs_dst[rec[0]]

                            # if rec_dst[2] and (u'%s' %
                            # rec_dst[2]).strip().lower() != (u'%s' %
                            # rec[1]).strip().lower():
                            new_value = rec[1]
                            if field_name_dst == 'reference_id':
                                new_value = reference_mapping.get(
                                    new_value, None)
                            else:
                                if new_value is None:
                                    new_value = ''
                            # print value_src

                            if rec_dst_value and (rec_dst_value != new_value):
                                print '\tWARNING: value is different (legacy_id #%s, "%s" <> "%s")' % (rec[0], rec[1], rec_dst_value)
                                continue

                            utils.sqlWrite(con_dst, ('update %s set %s = ' % (table_dst, field_name_dst)) + (
                                ' %s WHERE id = %s '), [new_value, rec_dst_id], self.is_dry_run())
                            # print 'update %s set %s = %s WHERE id = %s ' %
                            # (table_dst, field_name_dst, new_value,
                            # rec_dst_id)
                            written += 1

                        print '\t%s records changed. %s missing legacy records ' % (written, missing)

                    cur_src.close()
                    cur_dst.close()

        con_dst.commit()
        con_dst.leave_transaction_management()

        # ----------------------------------------------

        print 'B. Remove incorrect \'face\' value in ItemPart.'
        from digipal.models import ItemPart
        c = 0
        for model in ItemPart.objects.filter(locus='face'):
            model.locus = ''
            model.save()
            c += 1
        print '\t%d records changed' % c

        # ----------------------------------------------

        print '2a. fix \'abbrev.stroke,\' => \'abbrev. stroke\' in Character to match the Allograph.name otherwise we\'ll still have plenty of duplicates.'

        # fix 'abbrev.stroke,' => 'abbrev. stroke' otherwise we'll still have
        # duplicates
        from digipal.models import Character
        try:
            character = Character.objects.get(name='abbrev.stroke')
            character.name = 'abbrev. stroke'
            character.save()
        except Character.DoesNotExist:
            pass

        # ----------------------------------------------

        print '1., 2b., 3. Save all models to fix various labelling errors.'
        import digipal.models

        #model_class_names = [c for  c in dir(digipal.models) if re.search('^[A-Z]', c)]

        # These model classes are in order of dependency of the display_label
        # (B depends from A => A listed before B).
        model_class_names = '''
            Ontograph
            Allograph
            AllographComponent
            ScriptComponent
            Reference
            Owner
            CatalogueNumber
            HistoricalItem
            Description
            ItemOrigin
            Archive
            Repository
            CurrentItem
            Scribe
            Idiograph
            HistoricalItemDate
            ItemPart
            Image
            DateEvidence
            Graph
            PlaceEvidence
            Proportion
            '''
        model_class_names = re.findall('(\S+)', model_class_names)

        c = 0
        for model_class_name in model_class_names:
            c += 1
            model_class = getattr(digipal.models, model_class_name)
            models = model_class.objects.all().order_by('id')
            print '\t(%d / %d, %d records)\t%s' % (c, len(model_class_names), len(models), model_class._meta.object_name)
            for model in models:
                model.save()

        print 'WARNING: A. to be implemented when the pagination field contains the correct value.'

        print 'Done'

    def is_dry_run(self):
        return self.options.get('dry-run', False)

    def test(self, options):
        #from digipal.models import *
        from django.template.defaultfilters import slugify
        from digipal.templatetags.html_escape import update_query_string

        # content = '''  href="?k1=v1&k2=v2.1#anchor1=1" href="?k3=v3&k2=v2.2"  href="/home" '''
        #updates = '''k2=&k5=v5'''
        # print content
        # print update_query_string(content, updates)
#         from digipal.models import ItemPart
#         for ip in ItemPart.objects.all():
#             desc = ip.historical_item.get_display_description()
#             if desc:
#                 print ip.id, desc.source.name
#         url = '?id=93&result_type=scribes'
#         updates = 'terms=%C3%86thelstan&basic_search_type=hands&ordering=&years=&result_type=&scribes=&repository=&place=&date='
#         update_query_string(url, updates, True)

        url = '?page=2&amp;terms=%C3%86thelstan&amp;repository=&amp;ordering=&amp;years=&amp;place=&amp;basic_search_type=hands&amp;date=&amp;scribes=&amp;result_type='
        updates = 'result_type=manuscripts'
        update_query_string(url, updates, False)

#         slugs = {}
#         for allograph in Allograph.objects.all():
#             s = anchorify(u'%s' % allograph)
#             if s in slugs:
#                 print '>>>>>>>>>> ALREADY EXISTS'
#             slugs[s] = 1
#             print s, (u'%s' % allograph).encode('utf-8')
#
#         update_query_string(content, updates)

        # ST.id=253 => H.id=1150

        #rec = StewartRecord.objects.get(id=253)
        # rec.import_steward_record()

        # print
        # Hand.objects.filter(descriptions__description__contains='sema').count()

    def get_duplicate_cis(self):
        from digipal.models import CurrentItem
        duplicates = {}
        for ci in CurrentItem.objects.all():
            key = self.get_normalised_code(
                '%s-%s' % (ci.repository.id, ci.shelfmark))
            if key not in duplicates:
                duplicates[key] = []
            duplicates[key].append(ci)
        return duplicates

    ##################################################
    #
    #                PSEUDO ITEMS
    #
    ##################################################

    def find_pseudo_items(self, his):
        ips_conversion = {}
        his_to_delete = set()

        ip_count = 0

        for hi in his:
            print '%s' % self.get_obj_label(hi)
            cat_nums = hi.catalogue_numbers.all()
            other_cat_nums = ''
            if cat_nums.count() == 0:
                self.print_warning('HI with non-Sawyer number', 1)
                continue
            for cat in cat_nums:
                if cat.source.name not in self.get_pseudo_types():
                    self.print_warning(
                        'HI with non-Sawyer / Pelteret number', 1)
                    other_cat_nums = '\t\t%s' % ','.join(
                        ['%s' % cn for cn in hi.catalogue_numbers.all()])
                    continue
            if other_cat_nums:
                print other_cat_nums
                continue

            for ip in hi.item_parts.all().order_by('id'):
                ip_count += 1
                print '\t%s' % self.get_obj_label(ip)
                correct_ip = None
                # We also look for duplicates of the CIs (see JIRA-230)
                duplicate_cis = self.get_duplicates_of_current_item(
                    ip.current_item, True)
                correct_ips = list(ItemPart.objects.filter(current_item__in=duplicate_cis).exclude(
                    historical_items__historical_item_type__name='charter').order_by('id'))

                if len(correct_ips) == 0:
                    self.print_warning('no correct IP found', 2)
                    continue
                if len(correct_ips) == 1:
                    correct_ip = correct_ips[0]
                if len(correct_ips) > 1:
                    self.print_warning('more than one correct IP', 2)
                    for cip in correct_ips:
                        if self.loci_are_the_same(ip.locus, cip.locus):
                            if correct_ip:
                                self.print_warning(
                                    'more than one IP with the same locus', 2)
                            correct_ip = cip
                if correct_ip is None:
                    self.print_warning('no IP with same locus', 2)
                    print (u'\t\t\t%s <> %s' % (repr(ip.locus), u' | '.join(
                        repr(u'%s' % cip.locus) for cip in correct_ips)))
                    continue
                if not self.loci_are_the_same(ip.locus, correct_ip.locus):
                    self.print_warning(
                        'selected correct IP has a different locus', 2)
                    print '\t\t\t%s' % self.get_obj_label(correct_ip)
                    print u'\t\t\t%s <> %s' % (repr(ip.locus), repr(correct_ip.locus))
                    continue

                correct_hi = correct_ip.historical_item

                print '\t\t%s (Correct)' % self.get_obj_label(correct_hi)
                print '\t\t%s (Correct)' % self.get_obj_label(correct_ip)

                # create new text record based on the data in hi connected to
                # correct_ip
                ips_conversion[ip.id] = correct_ip.id
            his_to_delete.add(hi.id)
            # delete ip
            # delete hi

        return ips_conversion, his_to_delete, ip_count

    def loci_are_the_same(self, l1, l2):
        if not l1 and l2 == u'fols. 0\u20137':
            return True
        return self.get_normalised_code(l1) == self.get_normalised_code(l2)

    def protect_pseudo_his(self, ips_conversion, his_to_delete):
        his_to_keep = set()
        for ip in ItemPart.objects.exclude(id__in=ips_conversion.keys()).order_by('id'):
            hi_ids = set([hi.id for hi in ip.historical_items.all()])
            if hi_ids.issubset(his_to_delete):
                self.print_warning('IP will have no HI left', 0)
                print '\t%s' % self.get_obj_label(ip)
                for hi in HistoricalItem.objects.filter(id__in=hi_ids):
                    print '\t%s (cannot be deleted)' % self.get_obj_label(hi)
                    his_to_keep.add(hi.id)
                    # his_to_delete.remove(hi)

        his_to_delete = his_to_delete - his_to_keep

        return his_to_delete

    def get_pseudo_types(self):
        return [settings.SOURCE_SAWYER, settings.SOURCE_PELTERET]

    def create_text_records(self, ips_conversion, his_to_delete):
        # create the Texts
        # for hi in HistoricalItem.objects.filter(id__in=his_to_delete):
        for hi in HistoricalItem.objects.all():
            # Find or Create the text record

            # Get the HI Sawyer Cat Num
            hi_cat_nums = hi.catalogue_numbers.filter(
                source__name__in=self.get_pseudo_types())
            if hi_cat_nums.count() < 1:
                continue

            print self.get_obj_label(hi)

            if hi_cat_nums.count() > 1:
                print '\tNOTICE: more than one cat cum: %' % [', '.join('%s' % cat_num for cat_num in hi_cat_nums)]

            # Find a Text with the same Cat Num
            #texts = Text.objects.filter(Q(catalogue_numbers__source=hi_cat_num.source) & Q(catalogue_numbers__number=hi_cat_num.number))
            texts = list(Text.objects.raw(ur'''
                select distinct te.*
                from digipal_text te,
                digipal_cataloguenumber cn,
                digipal_cataloguenumber cn2
                where cn.historical_item_id = %s
                and cn.source_id in (5, 6)
                and cn2.source_id = cn.source_id
                and cn2.number = cn.number
                and cn2.text_id = te.id
            ''' % hi.id))

            if len(texts) == 0:
                print '\tCreate Text'
                # create the Text and cat num
                text = Text()
            if len(texts) == 1:
                print '\tUpdate Text'
                # update the text
                text = texts[0]
            if len(texts) > 1:
                self.print_warning(
                    'More than one Text with that cat number', 1)
                continue
            if not text.name:
                text.name = hi.display_label
            if not text.legacy_id:
                text.legacy_id = hi.legacy_id

            # Set the other fields (date, category, languages)
            text.date = hi.date
            text.save()

            # set the categories
            text.categories.clear()

            for category in hi.categories.all():
                print '\t\tCategory: %s' % category
                text.categories.add(category)

            # set the languages
            text.languages.clear()

            if hi.language:
                print '\t\tLanguage: %s' % hi.language
                text.languages.add(hi.language)

            # connect the text to the correct item part
            # Check what to do for
#             for ip in hi.item_parts.filter(id__in=ips_conversion.keys()):
#                 from django.db.utils import IntegrityError
#                 if not TextItemPart.objects.filter(text=text, item_part_id=ips_conversion[ip.id]).count():
#                     print '\t\tCorrect ItemPart: #%s' % ips_conversion[ip.id]
#                     TextItemPart(text=text, item_part_id=ips_conversion[ip.id]).save()

            for ip in hi.item_parts.all():
                correct_ip_id = ips_conversion.get(ip.id, ip.id)
                if not TextItemPart.objects.filter(text=text, item_part_id=correct_ip_id).count():
                    corrected = ''
                    if correct_ip_id != ip.id:
                        corrected = ' (corrected)'
                    print '\t\tItemPart: #%s%s' % (correct_ip_id, corrected)
                    TextItemPart(text=text, item_part_id=correct_ip_id).save()

            text.descriptions.clear()
            # create descriptions
            for description in hi.description_set.filter(source__name__in=self.get_pseudo_types()):
                print '\tCreate description'
                Description(source=description.source,
                            description=description.description, text=text).save()

            text.save()

            if len(texts) == 0:
                # create cat nums
                for hi_cat_num in hi_cat_nums:
                    CatalogueNumber(source=hi_cat_num.source,
                                    number=hi_cat_num.number, text=text).save()

    def process_pseudo_items(self):
        from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
        con = connections['default']
        con.enter_transaction_management()
        con.managed()
        con.disable_constraint_checking()

        # text.objects.all().delete()
        utils.fix_sequences(db_alias='default', silent=True)

        # See JIRA 86 and 223
        print '\n1. Find pseudo HIs and pseudo IPs\n'

        his = HistoricalItem.objects.filter(historical_item_type__name='charter').exclude(
            historical_item_format__name='Single-sheet').order_by('id')

        ips_conversion, his_to_delete, ip_count = self.find_pseudo_items(his)

        print '\n2. Find all non-deletable IPs which have only deletable HIs\n'

        his_to_delete = self.protect_pseudo_his(ips_conversion, his_to_delete)

        # Integrity check: no pseudo-IP can also be a correct IP
        ip_correct_and_pseudo = set(
            ips_conversion.keys()).intersection(ips_conversion.values())
        if len(ip_correct_and_pseudo):
            print 'ERROR: pseudo-IP = correct-IP'
            print ip_correct_and_pseudo
            return

        print '\n3. Create the Text records\n'

        self.create_text_records(ips_conversion, his_to_delete)

        print '\n4. Move Hands and Images from the pseudo-IPs to the correct IPs.\n'

        from digipal.models import Hand, Image

        for h in Hand.objects.filter(item_part_id__in=ips_conversion.keys()):
            print '\t%s' % self.get_obj_label(h)
            h.item_part_id = ips_conversion[h.item_part_id]
            h.save()

        for i in Image.objects.filter(item_part_id__in=ips_conversion.keys()):
            print '\t%s' % self.get_obj_label(i)
            i.item_part_id = ips_conversion[i.item_part_id]
            i.save()

        print '\n5. Delete pseudo-HIs and pseudo-CIs.\n'

        # delete the pseudo-HIs
        if 1:
            for hi in HistoricalItem.objects.filter(id__in=his_to_delete).order_by('id'):
                print '\tDelete %s' % self.get_obj_label(hi)
                hi.delete()

            # delete the pseudo-IPs
            for ip in ItemPart.objects.filter(id__in=ips_conversion.keys()).order_by('id'):
                print '\tDelete %s' % self.get_obj_label(ip)
                ip.delete()

        print '\n6. Summary\n'

        print '%s cartulary HIs, %s deleted HIs, %s item parts, %s deleted IP, %s correct IP.' % (his.count(), len(his_to_delete), ip_count, len(ips_conversion.keys()), len(set(ips_conversion.values())))

        if self.is_dry_run():
            con.rollback()
            print 'Nothing actually written (remove --dry-run option for permanent changes).'
        else:
            con.commit()
        con.leave_transaction_management()

        self.print_warning_report()

    def add_cartulary_his(self):
        from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
        from digipal.models import ItemPartItem
        con = connections['default']
        con.enter_transaction_management()
        con.managed()
        con.disable_constraint_checking()

        for hi in HistoricalItem.objects.filter(historical_item_type__name='charter', historical_item_format__name='Single-sheet'):
            ciids = {}
            for ip in hi.item_parts.all():
                ciids[ip.current_item.id] = 1
            if len(ciids) > 1:
                print '%s' % self.get_obj_label(hi)
                first = True
                for ip in hi.item_parts.all():
                    print '\t%s' % self.get_obj_label(ip)
                    if first:
                        print '\t\tSkip'
                        first = False
                        continue

                    # Clone the HI
                    print '\t\tClone HI'
                    hi_new = self.get_cloned_hi(hi)

                    # Reconnect the IP to the new HI
                    print '\t\tConnect cloned HI (%s) to IP (%s)' % (self.get_obj_label(hi_new), self.get_obj_label(ip))
                    ItemPartItem.objects.filter(
                        historical_item=hi, item_part=ip).delete()
                    ItemPartItem(historical_item=hi_new, item_part=ip).save()

        self.fix_imcomplete_clones()

        if self.is_dry_run():
            con.rollback()
            print 'Nothing actually written (remove --dry-run option for permanent changes).'
        else:
            con.commit()
        con.leave_transaction_management()

        self.print_warning_report()

    def fix_imcomplete_clones(self):
        # Cloning of the HI in add_cartulary_his() didn't copy the
        #     .catalogue_number field, collations and descriptions.
        # We address that here in a second pass.
        for hi in HistoricalItem.objects.filter(historical_item_type__name='charter', historical_item_format__name='Single-sheet'):
            if hi.catalogue_number:
                select = '''
                    select hi.*
                    from digipal_historicalitem hi,
                    digipal_cataloguenumber cn
                    where
                    cn.historical_item_id = hi.id
                    and hi.id <> %s
                    and (cn.number, cn.source_id) in (select cn2.number, cn2.source_id from digipal_cataloguenumber cn2 where cn2.historical_item_id = %s)
                ''' % (hi.id, hi.id)
                for hi_clone in HistoricalItem.objects.raw(select):
                    print '%s' % self.get_obj_label(hi)
                    print '\tclone: %s' % self.get_obj_label(hi_clone)
                    hi_clone.catalogue_number = hi.catalogue_number
                    hi_clone.save()

                    # create the description
                    hi_clone.description_set.all().delete()
                    for desc in hi.description_set.all():
                        print '\t\tCreate description'
                        Description(historical_item=hi_clone,
                                    source=desc.source,
                                    description=desc.description,
                                    text_id=desc.text_id,
                                    comments=desc.comments,
                                    summary=desc.summary
                                    ).save()

                    # create the collation
                    hi_clone.collation_set.all().delete()
                    for col in hi.collation_set.all():
                        print '\t\tCreate collation'
                        Collation(historical_item=hi_clone,
                                  fragment=col.fragment,
                                  leaves=col.leaves,
                                  front_flyleaves=col.front_flyleaves,
                                  back_flyleaves=col.back_flyleaves
                                  ).save()

    def get_cloned_hi(self, hi):
        ret = HistoricalItem()
        ret.display_label = hi.display_label

        ret.legacy_id = hi.legacy_id
        ret.historical_item_type = hi.historical_item_type
        ret.historical_item_format = hi.historical_item_format
        ret.date = hi.date
        ret.name = hi.name
        ret.hair = hi.hair
        ret.language = hi.language
        ret.url = hi.url
        ret.vernacular = hi.vernacular
        ret.neumed = hi.neumed
        ret.catalogue_number = hi.catalogue_number
        ret.legacy_reference = hi.legacy_reference

        ret.save()

        for cat in hi.categories.all():
            ret.categories.add(cat)

        for owner in hi.owners.all():
            ret.owners.add(owner)

        # cat num!
        # Have to copy all the cat nums!
        for cat_num in hi.catalogue_numbers.all():
            print '\t\t\tCreate cat num: %s' % cat_num
            CatalogueNumber(historical_item=ret,
                            number=cat_num.number, source=cat_num.source).save()

        # layout! None of them has a layout so we can ignore this part.
        if hi.layout_set.count() > 0:
            self.print_warning('Has layout', 2)

        if hi.itemorigin_set.count() > 0:
            self.print_warning('Has origin', 2)

        if hi.description_set.count() > 0:
            self.print_warning('Has description', 2)

        if hi.collation_set.count() > 0:
            self.print_warning('Has collation', 2)

        return ret

    def get_duplicates_of_current_item(self, ci, echo=False):
        if not hasattr(self, 'duplicate_cis'):
            self.duplicate_cis = self.get_duplicate_cis()
        key = self.get_normalised_code(
            '%s-%s' % (ci.repository.id, ci.shelfmark))
        ret = self.duplicate_cis[key][:]
        if len(ret) > 1 and echo:
            self.print_warning('Bridged CIs with similar names', 2)
            print '\t\t\t%s (key: %s)' % (', '.join([self.get_obj_label(ci) % ci for ci in ret]), key)
        return ret

    def get_normalised_code(self, code):
        # return re.sub(ur'\W+', ur'.', locus.lower().strip())
        code = code.lower()
        # For CUL and Oxford Bodleian we ignore the number between parenthesis
        # at the end
        if (code.startswith('20-')) or (code.startswith('43-')):
            code = re.sub(ur'\(\d+\)\s*$', ur'', code)
        code = re.sub(ur'(\s|,|\.|-|_|\u2013)+', ur'_', code)
        return code.replace('ii', '2').replace('i', '1').replace('latin', 'lat').replace('additional', 'add').replace('add', 'ad').strip()

    ##################################################

    def print_warning(self, message, indent=0):
        if not hasattr(self, 'messages'):
            self.messages = {}
        self.messages[message] = self.messages.get(message, 0) + 1
        print ('\t' * indent) + 'WARNING: ' + message

    def print_warning_report(self):
        print 'WARNINGS:'
        for message in getattr(self, 'messages', []):
            print '\t%6d: %s' % (self.messages[message], message)

    def get_obj_label(self, obj):
        return utils.get_obj_label(obj)

    def handle(self, *args, **options):

        self.options = options

        path = self.get_backup_path()
        if not path:
            raise CommandError(
                'Path variable DP_BACKUP_PATH not set in your settings file.')
        if not isdir(path):
            raise CommandError('Backup path not found (%s).' % path)

        if len(args) < 1:
            raise CommandError(
                'Please provide a command. Try "python manage.py help dpdb" for help.')
        command = args[0]

        self.args = args[1:]

        known_command = False

        if options['db'] not in settings.DATABASES:
            raise CommandError(
                'Database settings not found ("%s"). Check DATABASE array in your settings.py.' % options['db'])

        db_settings = settings.DATABASES[options['db']]

        if command == 'create_index':
            known_command = True
            self.create_index(self.args[0], *self.args[1:])

        if command == 'build':
            known_command = True
            self.show_build_info()

        if command == 'setbuild':
            known_command = True
            self.set_build_info()

        if command == 'test':
            known_command = True
            self.test(options)

        if command == 'drop_tables':
            known_command = True
            self.dropTables(options)

        if command == 'merge_rf':
            known_command = True
            self.merge_rf()

        if command == 'merge_frg':
            known_command = True
            self.merge_frg()

        if command == 'checkdata1':
            known_command = True
            self.checkData1(options)

        if command == 'tidyup1':
            known_command = True
            self.tidyUp1(options)

        if command == 'tables':
            known_command = True
            self.showTables(options)

        if command == 'version':
            known_command = True
            self.show_version()

        if command == 'cleanlocus':
            known_command = True
            args = list(args)
            args.pop(0)
            self.cleanlocus(args, options)

        if command == 'fixseq':
            # fix the sequence number for auto incremental fields (e.g. id)
            # Unfortunately posgresql import does not update them so we have to
            # run this after an import
            known_command = True

            c = utils.fix_sequences(options.get('db', 'default'), True)
            print "%d sequences fixed." % c

        if command == 'add_cartulary_his':
            known_command = True
            self.add_cartulary_his()

        if command == 'pseudo_items':
            known_command = True
            self.process_pseudo_items()

        if command == 'duplicate_cis':
            known_command = True
            duplicates = self.get_duplicate_cis()
            for key in duplicates:
                cis = duplicates[key]
                if len(cis) > 1:
                    print 'Duplicates: (%s)' % key
                    for ci in cis:
                        print '\t%s' % self.get_obj_label(ci)

        if command == 'list':
            known_command = True
            from os import listdir
            from os.path import isfile, join
            for file in listdir(path):
                if isfile(join(path, file)):
                    (file_base_name, extension) = os.path.splitext(file)
                    if extension == '.sql':
                        print file_base_name

        if command == 'restore':
            known_command = True
            if len(args) < 2:
                raise CommandError(
                    'Please provide the name of the backup you want to restore. Use "pyhon manage.py dpdb list".')

            file_base_name = args[1]
            file = os.path.join(path, file_base_name) + '.sql'
            if not os.path.isfile(file):
                raise CommandError('Backup not found (%s).' % file)

            arg_host = ''
            if db_settings['HOST']:
                arg_host = ' -h %s ' % db_settings['HOST']
            cmd = 'psql -q -U %s %s %s < %s > tmp' % (
                db_settings['USER'], arg_host, db_settings['NAME'], file)
            self.run_shell_command(cmd)

        if command == 'user':
            # user: list the users
            # user pass USERNAME: reset the password to 'pass'
            known_command = True

            from django.contrib.auth.models import User

            if len(args) == 1:
                for user in User.objects.all():
                    print '%s\t%s' % (user.id, user.username)

            if len(args) == 3:
                username = args[2]
                pwd = 'pass'
                if args[1] == 'pass':
                    users = User.objects.filter(username=username)
                    if users.count():
                        user = users[0]
                    else:
                        user = User()
                    user.username = username
                    user.set_password(pwd)
                    user.is_active = True
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()

                    print 'User %s. Password reset to "%s".' % (username, pwd)

        if command == 'backup':
            # backup
            known_command = True

            file_base_name = 'dp'
            if len(args) > 1:
                file_base_name = args[1]

            table_option = ''
            if options['table']:
                table_option = '--table=%s' % options['table']

            output_file = os.path.join(path, file_base_name + '.sql')
            arg_host = ''
            if db_settings['HOST']:
                arg_host = ' -h %s ' % db_settings['HOST']
            cmd = 'pg_dump -c %s -U %s %s -f "%s" %s ' % (
                table_option, db_settings['USER'], arg_host, output_file, db_settings['NAME'])
            self.run_shell_command(cmd)
            print 'Database saved to %s' % output_file

        if not known_command:
            raise CommandError('Unknown command: "%s".' % command)

    def create_index(self, table, *cols):
        from django.db import connections
        from django.db.utils import ProgrammingError
        con_dst = connections['default']
        for col in cols:
            try:
                sql = 'CREATE INDEX %s_%s ON %s (%s)' % (
                    table, col, table, col)
                utils.sqlWrite(con_dst, sql)
            except ProgrammingError, e:
                if 'already exists' in '%s' % e:
                    pass
                else:
                    print 'ERROR %s.%s (%s)' % (table, col, e)

    def show_build_info(self):
        from mezzanine.conf import settings
        settings.use_editable()
        print '%s, %s (branch %s)' % (settings.DP_BUILD_NUMBER, settings.DP_BUILD_TIMESTAMP, settings.DP_BUILD_BRANCH)

    def set_build_info(self):
        from mezzanine.conf import settings
        settings.use_editable()

        self.set_settings('DP_BUILD_NUMBER', settings.DP_BUILD_NUMBER + 1)
        from datetime import datetime
        self.set_settings('DP_BUILD_TIMESTAMP',
                          datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        self.set_settings('DP_BUILD_BRANCH', self.options['branch'].strip())
        self.show_build_info()

    def set_settings(self, name, value):
        ''' Set a Mezzanine settings variable in the database '''
        from mezzanine.conf.models import Setting
        s, created = Setting.objects.get_or_create(name=name)
        s.value = value
        print u'Set setting %s %s' % (name, value)
        s.save()
        from mezzanine.conf import settings

    def get_backup_path(self):
        ret = getattr(settings, 'DB_BACKUP_PATH', None)
        return ret

    def run_shell_command(self, command):
        ret = True
        try:
            res = os.system(command)
            if res != 0:
                raise Exception('Exit code %s' % (res, ))
        except Exception, e:
            # os.remove(input_path)
            raise CommandError(
                'Error executing command: %s (%s)' % (e, command))
        finally:
            # Tidy up by deleting the original image, regardless of
            # whether the conversion is successful or not.
            # os.remove(input_path)
            pass
        return ret
