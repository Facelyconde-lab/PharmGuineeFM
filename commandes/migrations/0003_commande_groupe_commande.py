import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commandes', '0002_commande_adresse_livraison'),
    ]

    operations = [
        migrations.AddField(
            model_name='commande',
            name='groupe_commande',
            field=models.UUIDField(default=uuid.uuid4, editable=False, db_index=True),
        ),
    ]
