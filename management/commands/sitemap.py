# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from digipal import models
from django.conf import settings
import os


class Command(BaseCommand):
    
    commands = ['write', 'info']
    
    sitemap_folder = 'sitemaps'
    
    help = """
Sitemap generator script
sitemap.py <command>
\nCommand:
\twrite: write the sitemaps
\tinfo : show information about the sitemap config
    """

    option_list = BaseCommand.option_list + (
        make_option('--command',
                    default='info',
                    help='Command to be executed'),
    )

    def handle(self, *args, **options):

        if len(args) < 1:
            raise CommandError(
                'Please provide a command. Try "python manage.py help sitemap" for help.')
        
        self.command = args[0]
        
        if self.command not in self.commands:
            raise CommandError(
                'Unknown command "%s", allowed commands are: %s' % (self.command, ', '.join(self.commands)))
        
        self.models = [m.lower() for m in getattr(settings, 'SITEMAP_MODELS', [])]
        #self.path = os.path.join(settings.PROJECT_ROOT, '../digipal/static')
        self.path = settings.STATIC_ROOT
        self.path_to_resource = getattr(settings, 'SITEMAP_PATH_TO_RESOURCE', '')
        self.path_to_sitemaps = os.path.join(self.path, self.sitemap_folder)
        
        if not self.models:
            raise CommandError(
                'Please provide the settings variable SITEMAP_MODELS to state which models should be used to generate the sitemaps')

        if not self.path_to_resource:
            raise CommandError(
                'Please provide the settings variable SITEMAP_PATH_TO_RESOURCE to state where to point the urls of the sitemap')

        # run command
        self.run_command()

    def run_command(self):
        if self.command == 'info':
            print 'Output directory: %s' % self.path_to_sitemaps
            print 'Models          : %s' % ', '.join(self.models)
            
        if self.command == 'write':
            if not self.path_to_sitemaps:
                os.mkdir(self.path_to_sitemaps)
    
            _models = self.get_models()
            for _model in _models:
                file_name = '%s.xml' % (_model.__name__).lower()
                xml = self.get_sitemap_by_model(_model)
                self.write_file(file_name, xml)
            index = self.get_index_xml(_models)
            self.write_file('index.xml', index)
        

    def get_models(self):
        model = None
        _models = []
        for member in dir(models):
            if member.lower() in self.models:
                model = getattr(models, member)
                _models.append(model)
        return _models

    def get_sitemap_by_model(self, model):
        records = model.objects.all()
        xml = self.get_resource_xml(records)
        return xml

    def get_resource_xml(self, records):
        s = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n'
        for record in records:
            s += '<url>\n'
            s += '\t<loc>%s</loc>\n' % (self.path_to_resource.rstrip('/') + record.get_absolute_url())
            s += '\t<lastmod>%s</lastmod>\n' % (record.modified)
            s += '\t<changefreq>weekly</changefreq>\n'
            # s += '\t<priority>0.5</priority>\n'
            s += '</url>\n'

        s += '</urlset>'

        return s

    def get_index_xml(self, models):
        s = '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for model in models:
            s += '\t<sitemap>\n'
            s += '\t\t<loc>%s/%s.xml</loc>\n' % (self.path_to_resource.rstrip('/') + settings.STATIC_URL + 'sitemaps', model.__name__.lower())
            s += '\t</sitemap>\n'
        s += '</sitemapindex>\n'
        return s

    def write_file(self, identifier, content):
        path_to_file = os.path.join(self.path_to_sitemaps, identifier)
        _file = open(path_to_file, 'w+')
        _file.write(content)
        _file.close()
        print 'Written %s' % path_to_file 
