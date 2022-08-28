# Generated by Django 4.0.6 on 2022-08-19 22:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0006_conceptstretagy'),
    ]

    operations = [
        migrations.CreateModel(
            name='Securities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=16, verbose_name='股票代码')),
                ('name', models.CharField(max_length=8, verbose_name='中文名称')),
            ],
            options={
                'db_table': 'securities',
            },
        ),
    ]
