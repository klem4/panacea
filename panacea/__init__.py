# coding: utf-8
__author__ = 'klem4'

VERSION = (0, 0, 3)
__version__ = '.'.join(map(str, VERSION))

from django.conf import settings
if settings.DEBUG:
    print "DEBUG: %s" % __version__