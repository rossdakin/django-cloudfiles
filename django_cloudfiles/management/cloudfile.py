import os
import cloudfiles
from django.core.management.base import CommandError
from django_cloudfiles.management.utils.progress_bar import ProgressBar
from django_cloudfiles.management.utils.string import format_bytes

class CloudFile(object):
    def __init__(self, local_path):
        self.local_path = local_path

    def upload(self, container, remote_filename, verbosity=1):
        size = os.path.getsize(self.local_path)
        number, mnemonic = format_bytes(size)
        if verbosity > 0:
            print "  %s (%u %s):" % (remote_filename, number, mnemonic)
            self.progress_bar = ProgressBar(total_ticks=73)
            self.progress_bar.start()
            callback = self.progress_bar.tick
        else:
            callback = None
        try:
            object = container.create_object(remote_filename)
            object.load_from_filename(self.local_path, callback=callback)
        except IOError, (errno, string):
            print ""
            raise CommandError("Problem uploading file '" + self.local_path +
                               "': " + string + " (IOError " + str(errno) + ")")
        except cloudfiles.errors.IncompleteSend:
            print ""
            raise CommandError("Incomplete send of file: " + self.local_path)
        except cloudfiles.errors.InvalidObjectName, string:
            print ""
            raise CommandError("Invalid object name: '" + string +
                               "' (local file: '" + self.local_path + "')")
        except cloudfiles.errors.InvalidObjectSize:
            print ""
            raise CommandError("Invalid size for file: " + self.local_path)
        if verbosity > 0:
            self.progress_bar.end()
        return size
