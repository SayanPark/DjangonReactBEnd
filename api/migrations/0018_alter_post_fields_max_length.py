from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_alter_user_first_name_alter_user_last_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='post',
            name='tags',
            field=models.CharField(max_length=100, default=''),
        ),
        migrations.AlterField(
            model_name='post',
            name='status',
            field=models.CharField(max_length=100, choices=[
                ('Active', 'Active'),
                ('Draft', 'Draft'),
                ('Disabled', 'Disabled'),
            ], default='Active'),
        ),
    ]
