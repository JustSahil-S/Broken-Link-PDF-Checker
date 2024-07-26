from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dismiss", views.dismiss, name="dismiss"),
    path("ignore", views.ignore, name="ignore"),
    path("update", views.update, name="update"),
    # MS: add url for getting all entries
    # MS: should also keep all entries with status code OK?
    path("dismissAction/<str:id>", views.dismissAction, name="actiondismiss"),
    path("ignoreAction/<str:id>", views.ignoreAction, name="actionignore"),
    path("brokenAction/<str:id>", views.brokenAction, name="actionbroken")
]