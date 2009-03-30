import socket
import cloudfiles
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django_cloudfiles import (USERNAME_SETTINGS_ATTR, API_KEY_SETTINGS_ATTR,
                               CONTAINER_SETTINGS_ATTR)
from django_cloudfiles.utils.progress_bar import ProgressBar
from django_cloudfiles.utils.writer import write

REQUIRED_OPTIONS = (
    {'name': 'username',
     'settings_attr': USERNAME_SETTINGS_ATTR},
    {'name': 'api_key',
     'settings_attr': API_KEY_SETTINGS_ATTR},
    {'name': 'container_name',
     'settings_attr': CONTAINER_SETTINGS_ATTR},
)

class Command(BaseCommand):
    help = "Publish files to Mosso's CloudFiles service and (optionally) CDN."
    option_list = BaseCommand.option_list + (
        make_option('-u', '--username', dest="username", default=None,
                    help="Your Mosso username. If not specified, settings." +
                    USERNAME_SETTINGS_ATTR + " is used"),
        make_option('-k', '--api_key', dest="api_key", default=None,
                    help="Your Mosso API key. If not specified, settings." +
                    API_KEY_SETTINGS_ATTR + " is used"),
        make_option('-c', '--container_name', dest="container_name",
                    default=None, help="The name of the container to upload " +
                    " files to. If not specified, settings." +
                    CONTAINER_SETTINGS_ATTR + " is used"),
        make_option('-r', '--create_container', action="store_true",
                    dest="create_container", default=False,
                    help="Create the container if it doesn't exist"),
        make_option('-p', '--make_public', action="store_true",
                    dest="make_public", default=False,
                    help="Make the container public if it's not already"),
    )
    requires_model_validation = False

    def _set_required_options(self, options, required=REQUIRED_OPTIONS):
        for option in required:
            name = option['name']
            settings_attr = option['settings_attr']
            if options.get(name, None) == None:
                try:
                    options[name] = getattr(settings, settings_attr)
                except:
                    raise CommandError("Missing " + name + ": please specify " +
                                       "this as a script option, or set " +
                                       settings_attr + " in your settings file")

    def _get_connection(self, username, api_key):
        write("Connecting to CloudFiles: ")
        try:
            conn = cloudfiles.get_connection(username=username, api_key=api_key)
            print "done"
            return conn
        except socket.gaierror, (n, desc):
            print "failed"
            raise CommandError("It looks like you aren't online (socket." +
                               "gaierror error " + str(n) + ": " + desc + ").")
        except cloudfiles.errors.AuthenticationFailed:
            print "failed"
            raise CommandError("Authentication failed for username '" +
                               username + "' and api_key '" + api_key + "'.")
        except cloudfiles.errors.AuthenticationError, string:
            print "failed"
            raise CommandError("An unspecified authentication error has " +
                               "occurred (" + string + ").")
        except cloudfiles.errors.InvalidUrl, string:
            print "failed"
            raise CommandError("Could not connect (" + string + ")")

    def _get_container(self, conn, name, create=False):
        try:
            write("Getting container %s: " % name)
            container = conn.get_container(name)
            print "done"
        except cloudfiles.errors.InvalidContainerName, string:
            print "failed"
            raise CommandError("Invalid container name: '" + string + "'")
        except cloudfiles.errors.NoSuchContainer, string:
            if create:
                write("must create: ")
                container = conn.create_container(name)
                print "created"
            else:
                print "failed"
                raise CommandError("The container '" + string + "' does not " +
                                   "exist. Please create this container, or " +
                                   "use the --create_container option to let " +
                                   "this script create it for you.")
        return container

    def _get_filenames(self):
        local_base = '/Users/Jenn/ross/WebDev/sites/myclasslibrary.com/public/media/'
        filenames = (
            { 'local': local_base + 'css/base.css',
              'remote': 'css/base.css',
            },
            { 'local': local_base + 'images/48x48_bookcase.png',
              'remote': 'images/48x48_bookcase.png',
            },
            { 'local': local_base + 'images/64x64_bookcase.png',
              'remote': 'images/64x64_bookcase.png',
            },
            { 'local': local_base + 'images/bookshelf.jpg',
              'remote': 'images/bookshelf.jpg',
            },
            { 'local': local_base + 'images/favicon.png',
              'remote': 'images/favicon.png',
            },
            { 'local': local_base + 'images/kampyle-en-blue-band-low-right.gif',
              'remote': 'images/kampyle-en-blue-band-low-right.gif',
            },
            { 'local': local_base + 'images/logo.png',
              'remote': 'images/logo.png',
            },
            { 'local': local_base + 'js/kampyle.js',
              'remote': 'js/kampyle.js',
            },
            { 'local': local_base + 'js/pngfix.js',
              'remote': 'js/pngfix.js',
            },
            { 'local': local_base + 'escher-sources/http___ajax.googleapis.com_ajax_libs_yui_2.7.0_build_reset-fonts-grids_reset-fonts-grids.css',
              'remote': 'escher-sources/http___ajax.googleapis.com_ajax_libs_yui_2.7.0_build_reset-fonts-grids_reset-fonts-grids.css',
            },
        )
        return filenames

    def _upload_file(self, container, remote_filename, local_filename):
        self.progress_bar = ProgressBar(total_ticks=73)
        self.progress_bar.start()
        try:
            object = container.create_object(remote_filename)
            object.load_from_filename(local_filename,
                                      callback=self.progress_bar.tick)
        except IOError, (errno, string):
            print ""
            raise CommandError("Problem uploading file '" + local_filename +
                               "': " + string + " (IOError " + str(errno) + ")")
        except cloudfiles.errors.IncompleteSend:
            print ""
            raise CommandError("Incomplete send of file: " + local_filename)
        except cloudfiles.errors.InvalidObjectName, string:
            print ""
            raise CommandError("Invalid object name: '" + string +
                               "' (local file: '" + local_filename + "')")
        except cloudfiles.errors.InvalidObjectSize:
            print ""
            raise CommandError("Invalid size for file: " + local_filename)
        self.progress_bar.end()

    def _upload_files(self, container, filenames):
        """
        @container: a container object into while the files should be uplaoded
        @filenames: a list of dictionaries with members 'local' and 'remote'
        """
        print "Uploading %d files:" % len(filenames)
        for i, fn in enumerate(filenames):
            print "(%d/%d) %s" % (i+1, len(filenames), fn['remote'])
            self._upload_file(container, fn['remote'], fn['local'])
        print "Finished uploading %d files." % len(filenames)

    def _check_public(self, container, make_public=False):
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
               "the CDN. You can use the --make_public option to allow " +
               "this script to make the container public for you.")
        return False

    def _check_uri(self, container):
        media_url = getattr(settings, 'MEDIA_URL', None)
        public_uri = container.public_uri() + '/'
        if media_url != public_uri:
            print "In your settings.py file, be sure to set:"
            print "    MEDIA_URL = '%s'" % public_uri
            print "  (currently) = '%s'" % media_url

    def handle(self, *args, **options):
        try:
            self._set_required_options(options)
            conn = self._get_connection(options['username'], options['api_key'])
            container = self._get_container(conn, options['container_name'],
                                            options['create_container'])
            self._upload_files(container, self._get_filenames())
            if self._check_public(container, options['make_public']):
                self._check_uri(container)
        except cloudfiles.errors.ResponseError, string:
            print ""
            raise CommandError("The remote service has returned an error: " +
                               string)
        except KeyboardInterrupt:
            print ""
            raise CommandError("Aborted by keyboard interrupt.")
        except socket.timeout, string:
            print ""
            raise CommandError("Socket timeout: " + string)
        except socket.error, (errno, string):
            print ""
            raise CommandError("Socket error " + str(errno) + ": " + string)
