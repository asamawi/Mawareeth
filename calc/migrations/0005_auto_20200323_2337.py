# Generated by Django 3.0.2 on 2020-03-23 20:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0004_heir_correction'),
    ]

    operations = [
        migrations.AddField(
            model_name='heir',
            name='corrected_share',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='heir',
            name='share',
            field=models.IntegerField(default=0),
        ),
    ]