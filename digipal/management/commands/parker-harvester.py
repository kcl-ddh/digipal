# -*- coding: utf-8 -*-

import urllib2, json, csv, os, base64, re, time
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

class Command(BaseCommand):
    help = """
        Parker Harvester script
        parker-harvester.py <command> <username> <password> <size> <input_csv> <folder_output>
        \n\tOptions:
        \t\t<command>:\tcommand to be executed test|download
        \t\t<username>:\tusername to authenticate to the Parker On The Web server
        \t\t<password>:\tpassword to authenticate to the Parker On The Web server
        \t\t<size>:\tsize of the images to download. Must be one among ["small", "medium", "large", "xlarge", "full", "thumb"]
        \t\t<input_csv>:\tname of the .csv file to be parsed
        \t\t<folder_output>:\tfolder where files will be downloaded
    """

    option_list = BaseCommand.option_list + (
        make_option('--command',
            default='test',
            help='Command to be executed'),
        make_option('--username',
            default='',
            help='Username to authenticate to the Parker On The Web server'),
        make_option('--password',
            default='',
            help='Password to authenticate to the Parker On The Web server'),
        make_option('--size',
            default='',
            help='Size of the images to download. Must be one among ["small", "medium", "large", "xlarge", "full", "thumb"]'),
        make_option('--csv-file',
            default=False,
            help='csv file to be parsed'),
        make_option('--output-folder',
            default=False,
            help='Folder where to store downloaded images'),
        )

    def handle(self, *args, **options):

        if len(args) < 1:
            raise CommandError('Please provide a command. Try "python manage.py help parker-harvester" for help.')

        self.command = args[0]
        self.username = args[1]
        self.password = args[2]
        self.size = args[3]
        self.input_csv = args[4]
        self.output_folder = args[5]

        # run command
        self.run_command()

    def run_command(self):
        # allowed sizes provided by the Parker APIs - if a wrong size is provided, raise an exception
        allowed_sizes = ["small", "medium", "large", "xlarge", "full", "thumb"]

        if self.size and self.size not in allowed_sizes:
            raise Exception('Size not valid. It should be one among these options:\n' + str(allowed_sizes))

        csv_dict = self.open_csv(self.input_csv)
        url_json_manifest = 'http://dms-data.stanford.edu/data/manifests/Parker/collection.json'

        manuscripts_csv = self.csv_to_array(csv_dict)
        manuscripts_shelfmark_csv = self.extract_shelfmarks(manuscripts_csv)
        selected_manuscripts = self.selected_manuscripts(manuscripts_csv)

        manuscripts_collection = self.lookup_collection_manifest(url_json_manifest, manuscripts_shelfmark_csv)
        output = self.lookup_manuscript_manifest(manuscripts_collection, selected_manuscripts)

        # making csv output file
        self.make_csv(output)

    def csv_to_array(self, csv_dict):
        # building array manuscripts contained in the csv file

        manuscripts_csv = []
        for i in csv_dict:
            manuscripts_csv.append(i)
        return manuscripts_csv

    def extract_shelfmarks(self, manuscripts_csv):
        manuscripts_shelfmark_csv = []
        for csv_manuscript in manuscripts_csv:

            shelfmark = re.sub(r'([\d]+)(.)*', r'\g<1>', csv_manuscript['Shelfmark'])

            if len(shelfmark) == 1:
                shelfmark = '00' + shelfmark
            elif len(shelfmark) == 2:
                shelfmark = '0' + shelfmark
            csv_manuscript_string = "%s MS %s" % (csv_manuscript['Repository'], shelfmark)

            if not csv_manuscript_string in manuscripts_shelfmark_csv:
                manuscripts_shelfmark_csv.append(csv_manuscript_string)
        return manuscripts_shelfmark_csv

    def selected_manuscripts(self, manuscripts_csv):
        selected_manuscripts = {}
        for csv_manuscript in manuscripts_csv:
            label = csv_manuscript['Selected']
            shelfmark = re.sub(r'([\d]+)(.)*', r'\g<1>', csv_manuscript['Shelfmark'])

            if len(shelfmark) == 1:
                shelfmark = '00' + shelfmark
            elif len(shelfmark) == 2:
                shelfmark = '0' + shelfmark

            if not shelfmark in selected_manuscripts:
                selected_manuscripts[shelfmark] = []
            if not label in selected_manuscripts[shelfmark]:
                label = re.sub(r'(p)*[^\w]*', '', label).lower().replace(' ','')
                selected_manuscripts[shelfmark].append(label)
        return selected_manuscripts

    def open_csv(self, file_name):

        # if the file .csv is not locally provided, raise an Exception

        if not os.path.isfile(file_name):
            raise Exception('Provide .csv file')
        else:
            csv_object = csv.DictReader(open(file_name))
        return csv_object

    def make_csv(self, output):

        with open("output.csv", 'wb') as outcsv:
            writer = csv.writer(outcsv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
            writer.writerow(['Repository', 'Shelfmark', 'Page', 'URL'])
            for item in output:
                writer.writerow([item[0], item[1], item[2], item[3]])

    def lookup_collection_manifest(self, url_json_file, manuscripts_csv):

        # getting colle+ctions manifest json
        try:
            request = urllib2.Request(url_json_file)
            json_file = urllib2.urlopen(request).read()
            json_object = json.loads(json_file.replace('\'', '"'))
        except Exception, e:
            print 'ERROR:'
            print 'Tried to Download %s' % (url_json_file)
        # list for storing final manuscripts array
        list_manuscripts = []

        for manuscript in json_object:
            if json_object[manuscript] in manuscripts_csv:
                obj = {}
                obj['manuscript'] = json_object[manuscript]
                index = manuscript.find('Parker')
                #url = manuscript[0: index] + 'data/manifests/' + manuscript[index: len(manuscript)]
                url = manuscript[0: index] + manuscript[index: len(manuscript)]
                obj['url'] = url
                list_manuscripts.append(obj)

        return list_manuscripts


    def lookup_manuscript_manifest(self, manuscripts_from_json, manuscripts_csv):
        output = []
        for manuscript in manuscripts_from_json:

            if self.command == 'test':
                print '\n---------------------------------------------'
                print 'Manuscript: %s' % (manuscript['manuscript'])
                print 'Manifest URL: %s' % (manuscript['url'])

            request = urllib2.Request(manuscript['url'])
            json_file = urllib2.urlopen(request).read()
            json_object = json.loads(json_file)
            shelfmark = re.sub(r'CCCC MS ([\d]+)(.)*', r'\g<1>', manuscript['manuscript'])

            # parsing json file
            sequences = json_object['sequences']

            for sequence in sequences:
                canvases = sequence['canvases']
                for canvas in canvases:
                    value_canvas = re.sub(r'(p|f)*[^\w]*', '', canvas['label']).lower().replace(' ','')
                    if value_canvas in manuscripts_csv[shelfmark]:
                        output_obj = []
                        output_obj.append("CCCC")
                        output_obj.append(shelfmark)
                        resources = canvas['resources']
                        for resource in resources:
                            url = resource['resource']['@id']
                            if self.size:
                                url += '_' + self.size
                            index = url.find('/image/') + len('/image/')
                            url = url[0:index] + 'app/' + url[index: len(url)]
                            url = url.replace('TC', 'NC')

                            # building output object
                            output_obj.append(canvas['label']) # page
                            output_obj.append(url)  # url
                            output.append(output_obj)

                            if self.command == 'test':
                                print "Label: ", canvas['label']
                                print "URL: ", url

                            if self.command == "download":
                                self.download(url, canvas['label'], manuscript['manuscript'])
                                #time.sleep(12)
                                time.sleep(1)
        return output

    def download(self, url, file_name, folder_name):

        image_file_name = self.output_folder + '/' + folder_name + '/' + file_name + '.' + self.size + '.jpg'

        if not os.path.isdir(self.output_folder):
            os.mkdir(self.output_folder)

        if not os.path.isdir(self.output_folder + '/' + folder_name):
            os.mkdir(self.output_folder + '/' + folder_name)

        if not os.path.isfile(image_file_name):

            # building request

            try:
                request = urllib2.Request(url)
                base64string = base64.encodestring('%s:%s' % (self.username, self.password))
                authheader =  "Basic %s" % base64string
                request.add_header("Authorization", authheader)

                # open a file and write image's data
                image_file = open(image_file_name, 'wb')
                image_data = urllib2.urlopen(request).read()
                image_file.write(image_data)
                image_file.close()

            except Exception, e:
                print 'ERROR: %s' % e
                print 'Tried to Download %s, %s (%s)' % (folder_name, file_name, url)

        else:
            return False
