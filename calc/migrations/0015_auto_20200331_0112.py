# Generated by Django 3.0.2 on 2020-03-30 22:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0014_auto_20200331_0013'),
    ]

    operations = [
        migrations.RenameField(
            model_name='heir',
            old_name='shortage_union_shares',
            new_name='shortage_union_share',
        ),
    ]
