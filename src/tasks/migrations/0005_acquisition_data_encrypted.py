# Generated by Django 3.2.16 on 2022-12-01 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_auto_20220302_2250'),
    ]

    operations = [
        migrations.AddField(
            model_name='acquisition',
            name='data_encrypted',
            field=models.BooleanField(default=False),
        ),
    ]
