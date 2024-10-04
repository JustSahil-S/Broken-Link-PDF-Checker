from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
import threading
import sys

RUNNING_DEVSERVER = (len(sys.argv) > 1 and sys.argv[1] == 'runserver')

if RUNNING_DEVSERVER:
    bgnd_thread = threading.Thread(target=views.bgnd_task, args=[])
    bgnd_thread.setDaemon(True)
    bgnd_thread.start()



urlpatterns = [
    path("", views.index, name="index"),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('smtpsettings/', views.smtpSettings_view, name='smtpsettings'),
    path("all", views.all, name="all"),
    path("dismiss", views.dismiss, name="dismiss"),
    path("ignore", views.ignore, name="ignore"),
    path("checkall", views.checkall, name="checkall"),
    path("download_excel", views.download_excel, name="download_excel"),
    path("recheckAction/<str:id>", views.recheckAction, name="actionrecheck"),
    path("dismissAction/<str:id>", views.dismissAction, name="actiondismiss"),
    path("cancelDismissAction/<str:id>", views.cancelDismissAction, name="actiondismissignore"),
    path("ignoreAction/<str:id>", views.ignoreAction, name="actionignore"),
    path("cancelIgnoreAction/<str:id>", views.cancelIgnoreAction, name="actioncancelignore"),
    path("settings/<str:id>", views.settings, name="settings"),
    path("manage/", views.manage, name="manage"),
]