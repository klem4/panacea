# coding: utf-8
from django.core.management.base import BaseCommand, CommandError
from panacea import invalidation


class Command(BaseCommand):
    help = "Usage: ./manage.py invalidate_nginx_cache all\n" \
               "./manage.py invalidate_nginx_cache alias <alias1 [alias2 alias3...]>\n" \
               "./manage.py invalidate_nginx_cache model <app.model1 [app.model2 app.model3...]>"

    def handle(self, *args, **options):
        if not args:
            raise CommandError("Wrong number of arguments, see --help")
        _type = list(args).pop(0)
        handler = getattr(self, 'handle_%s' % _type, None)
        if not handler:
            raise CommandError("Unknown handler: %s, see --help" % _type)

        deleted = handler(args) or []
        self.stdout.write("deleted keys:\n")
        for key in deleted:
            self.stdout.write("*** '%s'\n" % key)

    def handle_all(self, *args):
        return invalidation.invalidate_all()

    def handle_alias(self, *args):
        return invalidation.invalidate_alias(*args)

    def handle_model(self, *args):
        return invalidation.invalidate_model(*args)
