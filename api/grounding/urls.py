from django.urls import path

from . import views

urlpatterns = [
    path("sources", views.sources),
    path("sources/<slug:slug>/outline", views.outline),
    path("sources/<slug:slug>/ask", views.ask),
]
