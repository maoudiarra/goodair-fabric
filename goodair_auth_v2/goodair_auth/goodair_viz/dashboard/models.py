from django.db import models
from django.contrib.auth.models import User


class Profil(models.Model):
    """
    Extension du User Django avec un rôle GoodAir.
    Relation OneToOne : 1 User = 1 Profil.
    """

    ROLES = [
        ('admin',   'Administrateur'),  # accès total
        ('editeur', 'Éditeur'),         # lecture + exports
        ('viewer',  'Observateur'),     # lecture seule
    ]

    user  = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    role  = models.CharField(max_length=20, choices=ROLES, default='viewer')
    # Champ informatif — permet d'identifier le labo d'appartenance
    organisation = models.CharField(max_length=100, blank=True, default='GoodAir')

    class Meta:
        verbose_name        = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateurs'

    def __str__(self):
        return f"{self.user.username} [{self.get_role_display()}]"

    # ── Helpers de rôle ──
    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_editeur(self):
        return self.role in ('admin', 'editeur')

    @property
    def is_viewer(self):
        return True  # tous les rôles peuvent lire
