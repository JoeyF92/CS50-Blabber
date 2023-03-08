
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("new_post", views.new_post, name="new_post"),
    path("load_post/<int:page>/<str:page_type>", views.load_post, name="load_post"),
    path("likes/<int:post_id>/<str:action>", views.likes, name="likes"),
    path("following", views.following, name="following"),
    path("profile/<int:user_id>", views.profile, name="profile"),
    path("edit_post/<int:post_id>", views.profile, name="profile")
]
