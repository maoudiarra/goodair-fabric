from django.urls import path, include
from dashboard import views as auth_views

urlpatterns = [
    # ── Authentification ──
    path('login/',  auth_views.login_view,  name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    # ── Dashboard ──
    path('', include('dashboard.urls')),
]
