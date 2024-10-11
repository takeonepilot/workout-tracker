"""workout_tracker URL Configuration

Points our project to our workout application.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),  # Caminho para o painel de administração do Django
    path("", include("apps.workout.urls")),  # Inclui as URLs do app workout
]
if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
