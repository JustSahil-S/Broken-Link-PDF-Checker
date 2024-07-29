from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("all", views.all, name="all"),
    path("dismiss", views.dismiss, name="dismiss"),
    path("ignore", views.ignore, name="ignore"),
    #path("update", views.update, name="update"),
    path("checkall", views.checkall, name="checkall"),
    path("recheckAction/<str:id>", views.recheckAction, name="actionrecheck"),
    path("dismissAction/<str:id>", views.dismissAction, name="actiondismiss"),
    path("ignoreAction/<str:id>", views.ignoreAction, name="actionignore"),
    #path("brokenAction/<str:id>", views.brokenAction, name="actionbroken")
]