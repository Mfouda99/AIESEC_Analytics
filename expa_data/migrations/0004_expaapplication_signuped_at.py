# Generated by Django 5.1.7 on 2025-04-09 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expa_data', '0003_rename_application_id_expaapplication_ep_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='expaapplication',
            name='signuped_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
