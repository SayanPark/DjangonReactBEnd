from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_remove_bookmark_profile_remove_post_profile_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='otp',
            field=models.CharField(max_length=10, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='reset_token',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
    ]
