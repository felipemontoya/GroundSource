"""Root URL configuration.

Flat on purpose. How pipeline stages map onto Django apps is an open
decision (see ../AGENTS.md); this file should grow by including app
URLconfs once that decision is made, not by accumulating views.
"""

from django.urls import path

from . import health

urlpatterns = [
    path("", health.root),
    path("health", health.health),
]
