import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VisiteRecherche',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('session_key', models.CharField(blank=True, max_length=40)),
                ('patient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recherches', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Visite (recherche)',
                'verbose_name_plural': 'Visites (recherches)',
                'ordering': ['-date_creation'],
            },
        ),
    ]
