from django.urls import path

from . import views

urlpatterns = [
    path("", views.case_list, name="case_list"),
    path("cases/new/", views.case_create, name="case_create"),
    path("cases/<slug:reference>/close/", views.case_close, name="case_close"),
    path("cases/<slug:reference>/", views.case_detail, name="case_detail"),
]
