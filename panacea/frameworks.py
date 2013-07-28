# coding: utf-8

class RestFramework(object):
    @property
    def method(self):
        return self._get_method()

    @property
    def status_code(self):
        return self._get_status_code()

    @property
    def content_type(self):
        return self._get_content_type()


    def _get_method(self): raise NotImplementedError()
    def _get_status_code(self): raise NotImplementedError()
    def _get_content_type(self): raise NotImplementedError()


class DjangoRestFramework0x(RestFramework):
    pass


class DjangoRestFramework2x(RestFramework):
    pass

