from django.db import migrations, models
from django.utils import timezone
import datetime

class Migration(migrations.Migration):

    dependencies = [
    ('accounts', '0002_initial'), 
]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='rating',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='profile',
            name='joined_on',
            field=models.DateTimeField(
                default=timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profile',
            name='verified',
            field=models.BooleanField(default=False),
        ),
    ]
