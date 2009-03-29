import sys
import cloudfiles
from django_cloudfiles import *

#    from django.conf import settings
#
#    username = settings.MOSSO_USERNAME
#    api_key = settings.MOSSO_API_KEY
#    container_name = settings.CLOUDFILES_CONTAINER_NAME

def tick(t, s):
    print t * 100 / s

class Publisher(object):
    def _write(self, str):
        sys.stdout.write(str)
        sys.stdout.flush()        

    def _print_upload_tick(self):
        self._write("\b%s%s" % (RUN_TICK_CHAR, TIP_TICK_CHAR))
        self._upload_ticks_printed += 1

    def _upload_tick(self, transferred, size):
        percent = transferred * 100 / size # eliminate floating point division
        ticks_wanted_now = percent * UPLOAD_TICKS_WANTED / 100
        while self._upload_ticks_printed < ticks_wanted_now:
            self._print_upload_tick()

    def _upload_file(self, container, remote_filename, local_filename):
        # notify of file starting
        print "  %s" % remote_filename
        object = container.create_object(remote_filename)

        # begin progress notification and file upload
        self._write("  %s%s" % (BEGIN_TICK_CHAR, RUN_TICK_CHAR))
        self._upload_ticks_printed = 0
        object.load_from_filename(local_filename, callback=self._upload_tick)

        # finish off the progress bar
        while self._upload_ticks_printed < UPLOAD_TICKS_WANTED:
            self._print_upload_tick()
        print END_TICK_CHAR

    def _upload_files(self, container, filenames):
        """
        @filenames: a list of dictionaries with members 'local' and 'remote'
        """
        print "Uploading %d files:" % len(filenames)
        for fn in filenames:
            self._upload_file(container, fn['remote'], fn['local'])    
        print "Finished uploading %d files." % len(filenames)

    def publish_files(self, username, api_key, filenames, create=True,
                      make_public=True):
        """
        @username: your Mosso username
        @api_key: your Mosso API key
        @filenames: list of dictionaries, each with members 'local' and 'remote'
        @create: boolean, whether or not to create the container if not exist
        @make_public: boolean, whether or not to auto make the container public
        """
        print "Beginning publication."

        print "Connecting to CloudFiles...",
        conn = cloudfiles.get_connection(username=username, api_key=api_key)
        print "done."

        # get or create the container
        try:
            print "Getting container %s..." % container_name,
            container = conn.get_container(container_name)
            print "done."
        except cloudfiles.errors.NoSuchContainer:
            if create:
                print "must create:",
                container = conn.create_container(container_name)
                print "created."
            else:
                print "failed."
                raise cloudfiles.errors.NoSuchContainer(
                    "The container %s does not exist. Use create=True to " +
                    "create nonexistent containers." % container_name
                    )

        # upload files
        self._upload_files(container, filenames)

        # make container public
        if make_public and not container.is_public():
            print "Making container public."
            container.make_public()

        # remid to set public_uri, if not already
#        public_uri = container.public_uri()
#        if getattr(settings, PUBLIC_URI_SETTING_NAME, None) != public_uri:
#            print ("Be sure to set %s to %s in your setting.py file." %
#                   (PUBLIC_URI_SETTING_NAME, public_uri))

        # done
        print "Publication complete."

###
username = 'rossdakin'
api_key = '********************************' # keep your api key private!
container_name = 'myclasslibrary.com'
local_base = '/Users/rdakin/Desktop/pics'
filenames = (
    { 'local': local_base + '/smile.png',
      'remote': 'pics/smile.png',
    },
    { 'local': local_base + '/frown.jpg',
      'remote': 'pics/frown.jpg',
    },
    { 'local': local_base + '/cat.jpg',
      'remote': 'pics/cat.jpg',
    },
)
p = Publisher()
p.publish_files(username, api_key, filenames)
###
