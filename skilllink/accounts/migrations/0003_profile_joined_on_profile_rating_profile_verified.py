# accounts/migrations/0003_profile_fields.py
from django.db import migrations, models
import datetime

class Migration(migrations.Migration):

    dependencies = [
    ('accounts', '0002_initial'),  # <-- put the actual last migration name here
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
                auto_now_add=True,
                default=datetime.datetime(2025, 12, 11, 0, 0, tzinfo=datetime.timezone.utc)
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profile',
            name='verified',
            field=models.BooleanField(default=False),
        ),
    ]
