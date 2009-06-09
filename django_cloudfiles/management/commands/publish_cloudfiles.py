import socket
import time
import cloudfiles
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django_cloudfiles import (USERNAME_SETTINGS_ATTR, API_KEY_SETTINGS_ATTR,
                               CONTAINER_SETTINGS_ATTR,
                               LOCAL_FILES_ROOT_SETTINGS_ATTR)
from django_cloudfiles.management.cloudfile import CloudFile
from django_cloudfiles.management.connection import Connection
import django_cloudfiles.management.container as Container
from django_cloudfiles.management.utils.string import (write, format_bytes,
                                                       format_secs)
REQUIRED_OPTIONS = (
    {'name': 'username',
     'settings_attr': USERNAME_SETTINGS_ATTR},
    {'name': 'api_key',
     'settings_attr': API_KEY_SETTINGS_ATTR},
    {'name': 'container_name',
     'settings_attr': CONTAINER_SETTINGS_ATTR},
    {'name': 'local_root',
     'settings_attr': LOCAL_FILES_ROOT_SETTINGS_ATTR},
)

class Command(BaseCommand):
    help = "Publish files to Mosso's CloudFiles service and (optionally) CDN."
    option_list = BaseCommand.option_list + (
        make_option('-u', '--username', dest="username", default=None,
                    help="Your Mosso username. If not specified, settings." +
                    USERNAME_SETTINGS_ATTR + " is used"),
        make_option('-k', '--api-key', dest="api_key", default=None,
                    help="Your Mosso API key. If not specified, settings." +
                    API_KEY_SETTINGS_ATTR + " is used"),
        make_option('-c', '--container-name', dest="container_name",
                    default=None, help="The name of the container to upload " +
                    " files to. If not specified, settings." +
                    CONTAINER_SETTINGS_ATTR + " is used"),
        make_option('-r', '--local-root', dest="local_root",
                    default=None, help="Path to local root of files that " +
                    "you want to upload. If not specified, settings." +
                    LOCAL_FILES_ROOT_SETTINGS_ATTR + " is used"),
        make_option('-m', '--make-container', action="store_true",
                    dest="create_container", default=False,
                    help="Create the container if it doesn't exist"),
        make_option('-p', '--make-public', action="store_true",
                    dest="make_public", default=False,
                    help="Make the container public if it's not already"),
        make_option('-f', '--force', action="store_true", dest="force",
                    default=False, help="Upload files even if they haven't " +
                    "been modified since the last uplaod."),
    )
    requires_model_validation = False

    def _set_required_options(self, options, required=REQUIRED_OPTIONS):
        """
        Looks for required parameters in the settings file if they aren't given
        on the command line.
        """
        # while we're at it, make verbosity an int
        options['verbosity'] = int(options.get('verbosity', '1'))

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

    def _handle(self, *args, **options):
        conn = Connection(options['username'], options['api_key'])
        container = conn.get_container(options['container_name'],
                                       options['create_container'])

        print "Uploading files from '%s':" % options['local_root']
        start_time = time.time()
        count, bytes = Container.upload_tree(container, options['local_root'],
                                             force=options['force'],
                                             verbosity=options['verbosity'])
        stats = count, format_bytes(bytes), format_secs(time.time()-start_time)
        print "Finished uploading %u files (%s) in %s." % stats

        if Container.check_public(container, options['make_public']):
            Container.check_uri(container, getattr(settings, 'MEDIA_URL', None))

    def handle(self, *args, **options):
        """
        Wraps all command logic in some global exception handlers.
        """
        try:
            self._set_required_options(options)
            self._handle(*args, **options)
        except cloudfiles.errors.ResponseError, e:
            print ""
            raise CommandError("The remote service has returned an error: " +
                               str(e))
        except KeyboardInterrupt:
            print ""
            raise CommandError("Aborted by keyboard interrupt.")
        except socket.timeout, e:
            print ""
            raise CommandError("Socket timeout: " + str(e))
        except socket.error, (errno, e):
            print ""
            raise CommandError("Socket error " + str(errno) + ": " + str(e))
