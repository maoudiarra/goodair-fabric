from django.urls import path
from . import views

urlpatterns = [
    # Dashboard principal
    path('',                         views.index,           name='index'),
    # APIs — lecture (viewer, editeur, admin)
    path('api/aqi/',                 views.api_aqi,         name='api_aqi'),
    path('api/meteo/',               views.api_meteo,       name='api_meteo'),
    path('api/historique/',          views.api_historique,  name='api_historique'),
    path('api/predictions/',         views.api_predictions, name='api_predictions'),
    # API — admin uniquement
    path('api/qualite/',             views.api_qualite,     name='api_qualite'),
    # ── CRUD Utilisateurs (admin) ──
    path('admin/users/',             views.admin_users,     name='admin_users'),
    path('admin/users/create/',      views.user_create,     name='user_create'),
    path('admin/users/<int:uid>/edit/',    views.user_edit,   name='user_edit'),
    path('admin/users/<int:uid>/toggle/', views.user_toggle, name='user_toggle'),
    path('admin/users/<int:uid>/delete/', views.user_delete, name='user_delete'),
]
