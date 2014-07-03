# -*- coding: utf-8 -*-

from django.test import TestCase
from management.commands import _import_helper
from models import Hand, normalize_string


class AdminViewsTest(TestCase):

    def test_get_institution_type_from_category(self):
        """Tests parsing the institution type from the category."""
        expected = u'Abbey'

        category = u'Abbey'
        self.assertEqual(expected,
                _import_helper.get_institution_type_from_category(category))

        category = u'Abbey, then Cathedral'
        self.assertEqual(expected,
                _import_helper.get_institution_type_from_category(category))

        category = u'Abbey (until today)'
        self.assertEqual(expected,
                _import_helper.get_institution_type_from_category(category))

        category = ''
        self.assertIsNone(_import_helper.get_institution_type_from_category(category))

    def test_get_place_repository_shelfmark(self):
        """Tests the parsing of a legacy library name into three components:
        place name, repository, and shelfmark."""
        empty = ''
        expected_place = u'Oxford'
        expected_repository = u'Bodleian Library'
        expected_shelfmark = u'Norfolk Rolls'

        library = u'Oxford, Bodleian Library, Norfolk Rolls'
        place, repository, shelfmark = \
                _import_helper.get_place_repository_shelfmark(library)
        self.assertEqual(expected_place, place)
        self.assertEqual(expected_repository, repository)
        self.assertEqual(expected_shelfmark, shelfmark)

        library = u'[Oxford, Bodleian Library, Norfolk Rolls]'
        place, repository, shelfmark = \
                _import_helper.get_place_repository_shelfmark(library)
        self.assertEqual(expected_place, place)
        self.assertEqual(expected_repository, repository)
        self.assertEqual(expected_shelfmark, shelfmark)

        library = u'Oxford, Bodleian Library'
        place, repository, shelfmark = \
                _import_helper.get_place_repository_shelfmark(library)
        self.assertEqual(expected_place, place)
        self.assertEqual(expected_repository, repository)
        self.assertEqual(empty, shelfmark)

        library = u'[Oxford, Bodleian Library]'
        place, repository, shelfmark = \
                _import_helper.get_place_repository_shelfmark(library)
        self.assertEqual(expected_place, place)
        self.assertEqual(expected_repository, repository)
        self.assertEqual(empty, shelfmark)

        library = u''
        place, repository, shelfmark = \
                _import_helper.get_place_repository_shelfmark(library)
        self.assertIsNone(place)
        self.assertIsNone(repository)
        self.assertIsNone(shelfmark)

    def test_get_reference_name(self):
        """Tests the parsing of the reference value into a reference name."""
        value = u'{Bishop1, 1964--68 #263}'
        expected = u'Bishop1 1964–68'
        self.assertEqual(expected, _import_helper.get_reference_name(value))

        value = u'[Bishop2, 1964–68 #263]'
        expected = u'Bishop2 1964–68'
        self.assertEqual(expected, _import_helper.get_reference_name(value))

        value = u'Bishop3, 1964–68 #263'
        expected = u'Bishop3, 1964–68 #263'
        self.assertEqual(expected, _import_helper.get_reference_name(value))

    def test_get_references_from_scribe(self):
        """Test parsing multiple scribal references."""
        value = u'[Bishop, 1959--63 # @421--22]'
        expected = ['[Bishop, 1959--63 #]']
        self.assertEqual(expected,
                _import_helper.get_references_from_scribe(value))

        value = u'[Budny, 1997 #2 @460][Bishop, 1971 #34 @18][Dumville, 1993 #35 @54--55]'
        expected = ['[Budny, 1997 #2]',
                '[Bishop, 1971 #34]',
                '[Dumville, 1993 #35]']
        self.assertEqual(expected,
                _import_helper.get_references_from_scribe(value))

        value = u'[Budny, 1997 #2 @460]; [Bishop, 1971 #34 @18]; [Dumville, 1993 #35 @54--55]'
        expected = ['[Budny, 1997 #2]',
                '[Bishop, 1971 #34]',
                '[Dumville, 1993 #35]']
        self.assertEqual(expected,
                _import_helper.get_references_from_scribe(value))

    def test_get_null_boolean(self):
        """Tests the mapping between legacy database NullBollean and Django's
        NullBooleanField."""
        self.assertEqual(_import_helper.get_null_boolean(-1), True)
        self.assertEqual(_import_helper.get_null_boolean(0), False)
        self.assertEqual(_import_helper.get_null_boolean(1), None)


class ModelsTest(TestCase):

    def test_normalize_string(self):
        s = u'Munchen, Stadtarchiv'
        expected = 'munchen_stadtarchiv'
        self.assertEqual(normalize_string(s), expected)

        s = u'Braunschweig'
        expected = 'braunschweig'
        self.assertEqual(normalize_string(s), expected)

        s = u'St Gallen Stiftsbib.'
        expected = 'st_gallen_stiftsbib'
        self.assertEqual(normalize_string(s), expected)

        s = u'St Paul'
        expected = 'st_paul'
        self.assertEqual(normalize_string(s), expected)

        s = u'Dresden, Sachs.'
        expected = 'dresden_sachs'
        self.assertEqual(normalize_string(s), expected)
