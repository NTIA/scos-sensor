# Generated by Django 3.2.12 on 2022-04-20 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduleentry',
            name='action',
            field=models.CharField(help_text='[Required] The name of the action to be scheduled', max_length=50),
        ),
    ]
