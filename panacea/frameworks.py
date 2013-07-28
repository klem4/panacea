# coding: utf-8

class RestFramework(object):
    def __init__(self, request, response):
        self.request = request
        self.response = response


    @property
    def method(self):
        return self._get_method()

    @property
    def status_code(self):
        return self._get_status_code()

    @property
    def content_type(self):
        return self._get_content_type()


    def _get_method(self):
        raise NotImplementedError()

    def _get_status_code(self):
        raise NotImplementedError()

    def _get_content_type(self):
        raise NotImplementedError()


class DjangoRestFramework0x(RestFramework):
    def _get_method(self):
        return self.request.method

    def _get_status_code(self):
        return self.status_code

    def _get_content_type(self):
        # can raise IndexError, TypeError
        # TODO: проверить
        return self.response._headers.get('content-type')


class DjangoRestFramework2x(DjangoRestFramework0x):
    def _get_content_type(self):
        # can raise attribute error
        return self.response.accepted_media_type
