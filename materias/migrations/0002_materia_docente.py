# Generated migration for adding docente field to Materia model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('materias', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='materia',
            name='docente',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'rol': 'docente'},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='materias_asignadas',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Docente Asignado'
            ),
        ),
    ]
