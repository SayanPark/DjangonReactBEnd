# Generated by Django 5.2 on 2025-05-27 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_add_otp_and_reset_token_to_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='description',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
