from django.conf.urls import url
from . import views

app_name = 'MLPredictorPlatform'
urlpatterns = [
    url(r'^$', views.index_home, name='index1'),
    url(r'^login/$', views.login_user, name='login'),
    url(r'^registro/$', views.register, name='result'),
    url(r'^registro/completado/$', views.register_success, name='register_success'),
    url(r'^modelos/$', views.index, name='index'),
    url(r'^logout/', views.logout_view, name='logout'),
    url(r'^modelos/(?P<model_id>[0-9]+)/$', views.model_view, name='model'),
    url(r'^modelos/(?P<model_id>[0-9]+)/resultado$', views.model_result, name='result'),
    url(r'^modelos/subir$', views.upload_model, name='model_upload'),
    url(r'^modelos/(?P<model_id>[0-9]+)/eliminar', views.delete_model, name='delete'),
    url(r'^modelos/(?P<model_id>[0-9]+)/editar-vis', views.change_visibility, name='edit_visibility'),
    url(r'^modelos/seleccionar$', views.select_models, name='select_models'),
    url(r'^modelos/(?P<model_id>[0-9]+)/editar', views.edit_model, name='edit_model'),
]