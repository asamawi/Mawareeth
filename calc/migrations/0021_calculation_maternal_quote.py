# Generated by Django 3.0.5 on 2020-04-21 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0020_rename_2'),
    ]

    operations = [
        migrations.AddField(
            model_name='calculation',
            name='maternal_quote',
            field=models.BooleanField(default=False),
        ),
    ]
