from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

class DPBaseCommand(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--filter',
            action='store',
            dest='filter',
            default='',
            help='Only treat image names that contain the given string'),
        make_option('--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force changes despite warnings'),
        make_option('--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run, don\'t change any data.'),
        )
    
    def is_verbose(self):
        return self.get_verbosity() >= 2
    
    def get_verbosity(self):
        # 0: minimal output, 1: normal output, 2: verbose, 3: very verbose
        return int(self.options.get('verbosity', 1))

    def get_arg(self, i, default=None, error=None):
        ret = default
        if len(self.args) > i:
            ret = self.args[i]
        else:
            if error:
                print 'ERROR: %s' % error
                exit()
        return ret

    def is_dry_run(self):
        return self.options.get('dry-run', False)
