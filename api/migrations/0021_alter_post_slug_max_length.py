from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0020_alter_post_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='slug',
            field=models.SlugField(max_length=100, blank=True, null=True, unique=True),
        ),
    ]
