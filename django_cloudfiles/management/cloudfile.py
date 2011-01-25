import os
import sha
import cloudfiles
from django.core.management.base import CommandError
from django_cloudfiles.management.utils.progress_bar import ProgressBar
from django_cloudfiles.management.utils.string import format_bytes

MOD_HASH_NAME = 'django-cloudfiles-modified-hash'

class CloudFile(object):
    def __init__(self, container, remote_filename, local_path):
        self.container = container
        self.remote_filename = remote_filename
        self.local_path = local_path

        try:
            self.object = container.create_object(remote_filename)
        except cloudfiles.errors.InvalidObjectName, e:
            print ""
            raise CommandError("Invalid object name: '" + str(e) +
                               "' (local file: '" + self.local_path + "')")

    def get_local_size(self):
        return os.path.getsize(self.local_path)

    def generate_mod_hash(self):
        if getattr(self, "_cached_mod_hash", None):
            return self._cached_mod_hash
        hash_input = (self.remote_filename + str(self.get_local_size()) +
                      self.local_path + str(os.stat(self.local_path).st_mtime))
        self._cached_mod_hash = sha.new(hash_input).hexdigest()
        return self._cached_mod_hash

    def get_mod_hash(self):
        return self.object.metadata.get(MOD_HASH_NAME, None)

    def set_mod_hash(self, hash):
        self.object.metadata[MOD_HASH_NAME] = hash
        self.object.sync_metadata()

    def has_changed(self):
        return self.get_mod_hash() != self.generate_mod_hash()

    def upload(self, verbosity=1):
        if verbosity > 0:
            print "  %s (%s):" % (self.remote_filename,
                                  format_bytes(self.get_local_size()))
            if verbosity > 1:
                print "  %s = '%s'" % (MOD_HASH_NAME, self.generate_mod_hash())
            self.progress_bar = ProgressBar(total_ticks=73)
            self.progress_bar.start()
            callback = self.progress_bar.tick
        else:
            callback = None
        try:
            self.object.load_from_filename(self.local_path, callback=callback)
        except IOError, (errno, string):
            print ""
            raise CommandError("Problem uploading file '" + self.local_path +
                               "': " + string + " (IOError " + str(errno) + ")")
        except cloudfiles.errors.IncompleteSend:
            print ""
            raise CommandError("Incomplete send of file: " + self.local_path)
        except cloudfiles.errors.InvalidObjectSize:
            print ""
            raise CommandError("Invalid size for file: " + self.local_path)
        if verbosity > 0:
            self.progress_bar.end()

        self.set_mod_hash(self.generate_mod_hash())

        return self.get_local_size()
