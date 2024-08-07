from django.urls import path
from . import views
import threading


bgnd_thread = threading.Thread(target=views.bgnd_task, args=[])
bgnd_thread.setDaemon(True)
bgnd_thread.start()



urlpatterns = [
    path("", views.index, name="index"),
    path("all", views.all, name="all"),
    path("dismiss", views.dismiss, name="dismiss"),
    path("ignore", views.ignore, name="ignore"),
    #path("update", views.update, name="update"),
    path("checkall", views.checkall, name="checkall"),
    path("download_excel", views.download_excel, name="download_excel"),
    path("recheckAction/<str:id>", views.recheckAction, name="actionrecheck"),
    path("dismissAction/<str:id>", views.dismissAction, name="actiondismiss"),
    path("cancelDismissAction/<str:id>", views.cancelDismissAction, name="actiondismissignore"),
    path("ignoreAction/<str:id>", views.ignoreAction, name="actionignore"),
    path("cancelIgnoreAction/<str:id>", views.cancelIgnoreAction, name="actioncancelignore"),
    path("settings/<str:id>", views.settings, name="settings"),
    path("login", views.login_view, name="login"),    
    path("register", views.register, name="register"),

]