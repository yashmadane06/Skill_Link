from django.db import migrations
import cloudinary.models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_alter_profile_profile_pic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_pic',
            field=cloudinary.models.CloudinaryField(
                blank=True,
                null=True,
                max_length=255,
                verbose_name='image'
            ),
        ),
    ]
