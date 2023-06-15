# Generated by Django 4.2.1 on 2023-06-15 17:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_approvalrequests_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordReset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reset_code', models.IntegerField()),
                ('is_valid', models.BooleanField(default=False)),
                ('code_used', models.BooleanField(default=False)),
                ('date_requested', models.DateTimeField(auto_now_add=True)),
                ('grant_token', models.CharField(default='', max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
