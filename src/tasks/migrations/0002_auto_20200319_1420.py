# Generated by Django 3.0.4 on 2020-03-19 14:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tasks", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="acquisition",
            name="recording_id",
            field=models.IntegerField(
                default=1, help_text="The id of the recording relative to the task"
            ),
        )
    ]
