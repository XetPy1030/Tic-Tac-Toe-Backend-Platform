from django.urls import path

from .views import *

urlpatterns = [
    path('create', CreateView.as_view(), name='create'),

    path('external/meta', ExternalMetaView.as_view(), name='external_meta'),
    path('external/create', ExternalCreateView.as_view(), name='external_create'),
    path('external/finish/<uuid:game_id>', ExternalFinishView.as_view(), name='external_finish'),
]
