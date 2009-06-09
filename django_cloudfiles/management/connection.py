import socket
import cloudfiles
from django.core.management.base import CommandError
from django_cloudfiles.management.utils.string import write

class Connection(cloudfiles.Connection):
    def __init__(self, username, api_key, *args, **kwargs):
        """
        Wraps the constructor in some error handling and prints some messages.
        """
        write("Connecting to CloudFiles as '%s': " % username)
        try:
            super(Connection, self).__init__(username, api_key, *args, **kwargs)
            print "done"
        except socket.gaierror, (n, desc):
            print "failed"
            raise CommandError("It looks like you aren't online (socket." +
                               "gaierror error " + str(n) + ": " + desc + ").")
        except cloudfiles.errors.AuthenticationFailed:
            print "failed"
            raise CommandError("Authentication failed for username '" +
                               username + "' and api_key '" + api_key + "'.")
        except cloudfiles.errors.AuthenticationError, e:
            print "failed"
            raise CommandError("An unspecified authentication error has " +
                               "occurred (" + str(e) + ").")
        except cloudfiles.errors.InvalidUrl, e:
            print "failed"
            raise CommandError("Could not connect (" + str(e) + ")")

    def get_container(self, container_name, create=False):
        """
        Wraps this utility in some error handling and prints some messages.

        Also allows for the automatic creation of a container that doesn't
        exist yet, if create=True.
        """
        write("Getting container '%s': " % container_name)
        try:
            container = super(Connection, self).get_container(container_name)
            print "done"
        except cloudfiles.errors.InvalidContainerName, e:
            print "failed"
            raise CommandError("Invalid container name: '" + str(e) + "'")
        except cloudfiles.errors.NoSuchContainer, e:
            if create:
                write("must create: ")
                container = self.create_container(container_name)
                print "created"
            else:
                print "failed"
                raise CommandError("The container '" + str(e) + "' does not " +
                                   "exist. Please create this container, or " +
                                   "use the --make-container option to let " +
                                   "this script create it for you.")
        return container
