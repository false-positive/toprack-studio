# Generated by Django 5.2 on 2025-05-03 00:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datacenterspecs',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='module',
            name='name',
            field=models.CharField(max_length=255),
        ),
    ]
