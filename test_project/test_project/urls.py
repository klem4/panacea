from django.conf.urls import patterns, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from test_project.test_app import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'test_project.views.home', name='home'),
    # url(r'^test_project/', include('test_project.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    url(
        r'^api/promo/single/(?P<pk>\d+)/?$',
        views.APIPromoSingleView.as_view(),
        name='api_promo_single_empty_scheme'
    ),

    url(
        r'^api/promo/single/(?P<pk>\d+)/not_in_cache/?$',
        views.APIPromoSingleView.as_view(),
        name='api_promo_single_not_in_cache'
    ),

    url(
        r'^api/promo/single/(?P<pk>\d+)/first/?$',
        views.APIPromoSingleView.as_view(),
        name='api_promo_single_test_key_first'
    ),

    url(
        r'^api/promo/single/(?P<pk>\d+)/second/?$',
        views.APIPromoSingleView.as_view(),
        name='api_promo_single_test_key_second'
    ),

    url(
        r'^api/promo/list/?$',
        views.APIPromoListView.as_view(),
        name='api_promo_list'
    )
)
