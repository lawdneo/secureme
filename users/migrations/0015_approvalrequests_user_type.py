# Generated by Django 4.2.1 on 2023-07-09 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_station_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='approvalrequests',
            name='user_type',
            field=models.CharField(choices=[('police', 'Police Station'), ('analytics', 'Analytics Team'), ('admin', 'Admin')], default='analytics', max_length=10),
        ),
    ]
