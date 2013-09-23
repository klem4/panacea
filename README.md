django-panacea [![Build Status](https://travis-ci.org/klem4/panacea.png?branch=master)](https://travis-ci.org/klem4/panacea)
=======
django caching middleware, based on django-cacheops for using with httpredis nginx module

*In Greek mythology, Panacea (Greek Πανάκεια, Panakeia) was a goddess of Universal remedy*


Проект представляет собой приложение django, которое имеет в своем составе middleware, позволяющий средствами django-cacheops
сохранять в redis полный ответ, сгенерированный django-view, при этом, благодаря использованию [django-cacheops](https://github.com/Suor/django-cacheops "django-cacheops") , привязывать
ключ, под которым сохраняется контент к конъюнкциями заданных моделей, что дает возможность шибкой инвалидации данного кеша.
Формат ключа, под которым происходит сохранение контента в redis является "понятным" для регулярных выражений nginx, в результате
чего и происходит вторая часть магии: достовать закешированные ответы в дальнейшем сможет непосредственно nginx, благодаря модулю [HttpRedis](http://wiki.nginx.org/HttpRedis)

[django-cacheops](https://github.com/Suor/django-cacheops "django-cacheops") + [HttpRedis(Nginx)](http://wiki.nginx.org/HttpRedis) = **django-panacea**

## Установка
Последнюю стабильную версию можно поставить из pip:

`pip install django-panacea==0.1.2`

Никаких зависимостей за собой не тянет, но для работы естественно необходимо окружение в виде:
 - django >= 1.4.3
 - django-cacheops >= 1.0.0
 - django-rest-franework >= 2.3.6(на этом фреймворке я использую panacea), в теории, возможно использования любых других 
совместимых с django фреймворков, но для этого возможно потребуются небольшие доработки, связанные с получение данных из объекта
response(таких как куки, аргументы query_string и прочее, если класс объекта response далеко ушел от стандартного джанговского,
нужно будет допилить)

Полную матрицу тестирования можно посмотреть (тут)[https://github.com/klem4/panacea/blob/master/.travis.yml]

## Настройка
Для включения в работе необходимо внести изменения в *settings.py* вашего проекта:
 - Добавить panacea в список приложени: 

`INSTALLED_APPS.append('panacea')`

 - Добавить middleware в список мидлвейров(желательно поближе к началу списка, так как обратка ответа
 идет по списку мидлвейров снизу в вверх): 

`MIDDLEWARE_CLASSES.insert(0, 'panacea.middleware.NginxRedisCachingMiddleware')`

