from django.db import migrations, models
import django.utils.timezone

def set_default_date(apps, schema_editor):
    User = apps.get_model('api', 'User')
    for user in User.objects.filter(date__isnull=True):
        user.date = django.utils.timezone.now()
        user.save(update_fields=['date'])

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_remove_articleimage_article_remove_postimage_post_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.RunPython(set_default_date, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='date',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
