import os
import cloudfiles
from django.core.management.base import CommandError
from django_cloudfiles.management.utils.progress_bar import ProgressBar
from django_cloudfiles.management.utils.string import format_bytes

class CloudFile(object):
    def __init__(self, local_path):
        self.local_path = local_path

    def upload(self, container, remote_filename):
        size = os.path.getsize(self.local_path)
        number, mnemonic = format_bytes(size)
        print "  %s (%u %s):" % (remote_filename, number, mnemonic)
        self.progress_bar = ProgressBar(total_ticks=73)
        self.progress_bar.start()
        try:
            object = container.create_object(remote_filename)
            object.load_from_filename(self.local_path,
                                      callback=self.progress_bar.tick)
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
        self.progress_bar.end()
        return size
