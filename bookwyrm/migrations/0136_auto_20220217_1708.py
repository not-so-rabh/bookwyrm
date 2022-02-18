# Generated by Django 3.2.12 on 2022-02-17 17:08

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("bookwyrm", "0135_auto_20220217_1624"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="admin_code",
            field=models.CharField(default=uuid.uuid4, max_length=50),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="install_mode",
            field=models.BooleanField(default=False),
        ),
    ]