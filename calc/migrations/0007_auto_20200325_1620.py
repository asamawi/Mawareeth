# Generated by Django 3.0.2 on 2020-03-25 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0006_auto_20200324_1554'),
    ]

    operations = [
        migrations.AddField(
            model_name='calculation',
            name='shares_shorted',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='calculation',
            name='shortage',
            field=models.BooleanField(default=False),
        ),
    ]
