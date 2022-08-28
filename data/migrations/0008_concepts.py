# Generated by Django 4.0.6 on 2022-08-26 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0007_securities'),
    ]

    operations = [
        migrations.CreateModel(
            name='Concepts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=16, verbose_name='概念板块代码')),
                ('name', models.CharField(max_length=8, verbose_name='概念板块名称')),
            ],
            options={
                'db_table': 'concepts',
            },
        ),
    ]