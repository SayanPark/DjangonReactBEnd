from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_alter_post_fields_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='slug',
            field=models.SlugField(unique=True, null=True, blank=True, max_length=100),
        ),
    ]
