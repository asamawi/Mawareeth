# Generated by Django 3.0.2 on 2020-04-12 06:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0016_auto_20200412_0723'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marriage',
            name='female',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='female', to='calc.Person'),
        ),
        migrations.AlterField(
            model_name='marriage',
            name='male',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='male', to='calc.Person'),
        ),
    ]
