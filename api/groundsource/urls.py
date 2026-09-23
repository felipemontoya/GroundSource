"""Root URL configuration.

Flat at the top, with one app included beneath it. How pipeline stages map
onto Django apps is still open (see ../AGENTS.md); `grounding` is one app
because the proof of concept needs one, not because the shape is decided.
"""

from django.urls import include, path

from . import health

urlpatterns = [
    path("", health.root),
    path("health", health.health),
    path("", include("grounding.urls")),
]
