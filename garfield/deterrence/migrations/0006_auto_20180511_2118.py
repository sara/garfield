# Generated by Django 2.0.4 on 2018-05-11 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deterrence', '0005_deterrencemessage_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deterrent',
            name='image',
            field=models.ImageField(upload_to='static/deterrents/'),
        ),
    ]