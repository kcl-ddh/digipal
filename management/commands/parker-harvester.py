import urllib2, json, csv, os, base64, re
from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
    help = """
        Parker Harvester script
        parker-harvester.py <username> <password> <size> <input_csv> <dry_run>
        \n\tOptions:
        \t\t<username>:\tusername to authenticate to the Parker On The Web server
        \t\t<password>:\tpassword to authenticate to the Parker On The Web server
        \t\t<size>:\tsize of the images to download. Must be one among ["small", "medium", "large", "xlarge", "full", "thumb"]
        \t\t<input_csv>:\tname of the .csv file to be parsed
        \t\t<dry_run>:\ta boolean to specify whether download the images or not
    """

    option_list = BaseCommand.option_list + (
        make_option('--username',
            default='',
            help='username to authenticate to the Parker On The Web server'),
        make_option('--password',
            default='',
            help='password to authenticate to the Parker On The Web server'),
        make_option('--size',
            default='',
            help='size of the images to download. Must be one among ["small", "medium", "large", "xlarge", "full", "thumb"]'),
        make_option('--csv-file',
            default=False,
            help='csv file to be parsed'),
        make_option('--output-folder',
            default=False,
            help='folder where to store downloaded images'),
        make_option('--dry-run',
            default=False,
            help='a boolean to specify whether download the images or not')
        )

    def handle(self, *args, **options):

        self.username = args[0]
        self.password = args[1]
        self.size = args[2]
        self.input_csv = args[3]
        self.output_folder = args[4]

        if args < 4:
            self.dry_run = True
        else:
            self.dry_run = args[5]

        # allowed sizes provided by the Parker APIs
        # if a wrong size is provided, raise an exception
        allowed_sizes = ["small", "medium", "large", "xlarge", "full", "thumb"]

        if self.size and self.size not in allowed_sizes:
            raise Exception('Size not valid. It should be one among these options:\n' + str(allowed_sizes))

        csv_object = self.open_csv(self.input_csv)
        url_json_manifest = 'http://dms-data.stanford.edu/data/manifests/Parker/collection.json'

        # building array manuscripts contained in the csv file
        manuscripts_csv = []
        for i in csv_object:
            manuscripts_csv.append(i)

        manuscripts_shelfmark_csv = []
        for csv_manuscript in manuscripts_csv:
            shelfmark = re.sub(r'([\d]+)(.)*', r'\g<1>', csv_manuscript['Shelfmark'])
            csv_manuscript_string = "%s MS %s" % (csv_manuscript['Repository'], shelfmark)
            if not csv_manuscript_string in manuscripts_shelfmark_csv:
                manuscripts_shelfmark_csv.append(csv_manuscript_string)

        selected_manuscripts = {}
        for csv_manuscript in manuscripts_csv:
            label = csv_manuscript['Selected']
            shelfmark = re.sub(r'([\d]+)(.)*', r'\g<1>', csv_manuscript['Shelfmark'])
            if not shelfmark in selected_manuscripts:
                selected_manuscripts[shelfmark] = []
            if not label in selected_manuscripts[shelfmark]:
                label = re.sub(r'(p)*[^\w]*', '', label).lower().replace(' ','')
                selected_manuscripts[shelfmark].append(label)

        manuscripts_collection = self.lookup_collection_manifest(url_json_manifest, manuscripts_shelfmark_csv)
        self.lookup_manuscript_manifest(manuscripts_collection, selected_manuscripts)


    def open_csv(self, file_name):

        # if the file .csv is not locally provided, raise an Exception

        if not os.path.isfile(file_name):
            raise Exception('Provide .csv file')
        else:
            csv_object = csv.DictReader(open(file_name))
        return csv_object

    def lookup_collection_manifest(self, url_json_file, manuscripts_csv):

        # getting colle+ctions manifest json
        request = urllib2.Request(url_json_file)
        json_file = urllib2.urlopen(request).read()
        json_object = json.loads(json_file.replace('\'', '"'))

        # list for storing final manuscripts array
        list_manuscripts = []

        for manuscript in json_object:
            if json_object[manuscript] in manuscripts_csv:
                obj = {}
                obj['manuscript'] = json_object[manuscript]
                index = manuscript.find('Parker')
                url = manuscript[0: index] + 'data/manifests/' + manuscript[index: len(manuscript)]
                obj['url'] = url
                list_manuscripts.append(obj)

        return list_manuscripts


    def lookup_manuscript_manifest(self, manuscripts_from_json, manuscripts_csv):
        output = {}
        m = 0
        for manuscript in manuscripts_from_json[:5]:

            print '\n---------------------------------------------'
            print 'Manuscript: %s' % (manuscript['manuscript'])
            print 'Manifest URL: %s' % (manuscript['url'])

            request = urllib2.Request(manuscript['url'])
            json_file = urllib2.urlopen(request).read()
            json_object = json.loads(json_file)
            shelfmark = re.sub(r'CCCC MS ([\d]+)(.)*', r'\g<1>', manuscript['manuscript'])
            # parsing json file
            sequences = json_object['sequences']
            if not shelfmark in output:
                output[shelfmark] = []
            for sequence in sequences:
                canvases = sequence['canvases']
                for canvas in canvases:
                    value_canvas = re.sub(r'(p|f)*[^\w]*', '', canvas['label']).lower().replace(' ','')
                    output[shelfmark].append(value_canvas)
                    if value_canvas in manuscripts_csv[shelfmark]:
                        m += 1
                        resources = canvas['resources']
                        for resource in resources:
                            url = resource['resource']['@id']
                            if self.size:
                                url += '_' + self.size
                            index = url.find('/image/') + len('/image/')
                            url = url[0:index] + 'app/' + url[index: len(url)]
                            print "Label: ", canvas['label']
                            print "URL: ", url
                            if self.dry_run == "True":
                                self.download(url, canvas['label'] + '.jpg')

    def download(self, url, filename):

        # building request
        request = urllib2.Request(url)
        base64string = base64.encodestring('%s:%s' % (self.username, self.password))
        authheader =  "Basic %s" % base64string
        request.add_header("Authorization", authheader)

        if not os.path.isdir(self.output_folder):
            os.mkdir(self.output_folder)

        print os.path.isdir(self.output_folder)
        # open a file and write image's data
        image_file = open(self.output_folder + '/' + filename, 'wb')
        image_data = urllib2.urlopen(request).read()
        image_file.write(image_data)