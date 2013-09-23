django-panacea [![Build Status](https://travis-ci.org/klem4/panacea.png?branch=master)](https://travis-ci.org/klem4/panacea)
=======

*In Greek mythology, Panacea (Greek Πανάκεια, Panakeia) was a goddess of Universal remedy*

[django-cacheops](https://github.com/Suor/django-cacheops "django-cacheops") + [HttpRedis(Nginx)](http://wiki.nginx.org/HttpRedis) = **django-panacea**

Проект представляет собой приложение django, которое имеет в своем составе middleware, позволяющий средствами django-cacheops
сохранять в redis полный ответ, сгенерированный django-view, при этом, благодаря использованию django-cacheops, привязывать
ключ, под которым сохраняется контент к конъюнкциями заданных моделей, что дает возможность шибкой инвалидации данного кеша.
Формат ключа, под которым происходит сохранение контента в redis является "понятным" для регулярных выражений nginx, в результате
чего и происходит вторая часть магии: достовать закешированные ответы в дальнейшем сможет непосредственно nginx, благодаря модулю [HttpRedis(Nginx)](http://wiki.nginx.org/HttpRedis)

