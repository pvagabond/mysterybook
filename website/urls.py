from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from tastypie.api import Api
from store.api import ReviewResource

v1_api = Api(api_name='v1')
v1_api.register(ReviewResource())

urlpatterns = [
    # Examples:
    # url(r'^$', 'bookstore.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^store/', include('store.urls'), name='store'),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'^api/', include(v1_api.urls)),
    url(r'^admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

