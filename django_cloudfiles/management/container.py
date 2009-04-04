import os
import cloudfiles
from django.core.management.base import CommandError
from django_cloudfiles import is_ignored_path, URL_SEPERATOR
from django_cloudfiles.management.utils.string import write
from .cloudfile import CloudFile

class Container(object):
    """
    Just a namespace; don't instantiate.
    """
    @staticmethod
    def check_public(container, make_public=False):
        """
        Returns true if:
         1) The container is public, or
         2) The container is made public using the make_public param
        """
        if container.is_public():
            return True
        if make_public:
            write("Making container public: ")
            try:
                container.make_public()
                print "done"
                return True
            except CDNNotEnabled:
                print "failed (CDN is not available for your account)."
        print ("*** WARNING: Container is not public. Ensure that it's " +
               "made public, or your files will not be available over " +
               "the CDN. You can use the --make-public option to allow " +
               "this script to make the container public for you.")
        return False

    @staticmethod
    def check_uri(container, media_url):
        public_uri = container.public_uri() + '/'
        if media_url != public_uri:
            print "In your settings.py file, be sure to set:"
            print "    MEDIA_URL = '%s'" % public_uri
            print "  (currently) = '%s'" % media_url

    @classmethod
    def upload_tree(klass, container, tree_root, drop_remote_prefix=None):
        """
        Upload a tree of files rooted at tree_root to a specified container,
        skipping any local paths that match a pattern in IGNORE_PATTERNS_FLAGS.
        Symbolic links are followed, so make sure you don't have any loops!

        Remote file names are the local file names with seperator changed to
        URL_SEPERATOR and the tree_root dropped from the beginning.

        Returns the number of files uploaded and total bytes transfered (tuple).
        """
        count = 0
        bytes = 0
        tree_root = os.path.abspath(tree_root)
        tree_root = os.path.normpath(tree_root)
        if not (os.path.exists(tree_root) and
                os.path.isdir(tree_root)):
            raise CommandError("Not a valid directory: " + tree_root)
        if not drop_remote_prefix:
            drop_remote_prefix = tree_root
        for root, dirs, files in os.walk(tree_root):
            if is_ignored_path(root):
                continue
            for filename in files:
                path = os.path.join(root, filename)
                if is_ignored_path(path):
                    continue
                count += 1
                remote_filename = path[len(drop_remote_prefix)+1:]
                if os.sep != URL_SEPERATOR:
                    remote_filename.replace(os.sep, URL_SEPERATOR)
                cf = CloudFile(path)
                bytes += cf.upload(container, remote_filename)
            # os.walk doesn't follow linked subdirectories (potential infinite
            # loop) before Python 2.6, so we recurse over them manually:
            for dir in dirs:
                path = os.path.join(root, dir)
                if os.path.islink(path):
                    stats = klass.upload_tree(container, path,
                                              drop_remote_prefix)
                    count += stats[0]
                    bytes += stats[1]
        return count, bytes
