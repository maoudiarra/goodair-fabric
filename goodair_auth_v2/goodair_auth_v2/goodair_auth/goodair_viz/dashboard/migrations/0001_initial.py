from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profil',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(
                    choices=[('admin', 'Administrateur'), ('editeur', 'Éditeur'), ('viewer', 'Observateur')],
                    default='viewer', max_length=20
                )),
                ('organisation', models.CharField(blank=True, default='GoodAir', max_length=100)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profil',
                    to='auth.user'
                )),
            ],
            options={
                'verbose_name': 'Profil utilisateur',
                'verbose_name_plural': 'Profils utilisateurs',
            },
        ),
    ]
