from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medicaments', '0002_medicament_cle_recherche'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicament',
            name='dosage',
            field=models.CharField(blank=True, help_text='Ex : 500mg, 1g/5ml', max_length=50),
        ),
    ]
