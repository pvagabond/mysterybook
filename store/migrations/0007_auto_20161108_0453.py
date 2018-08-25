# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import store.models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_book_cover_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='latitude',
            field=models.FloatField(default=b'37.419', max_length=20),
        ),
        migrations.AddField(
            model_name='review',
            name='longitude',
            field=models.FloatField(default=b'122.05', max_length=20),
        ),
        migrations.AlterField(
            model_name='book',
            name='cover_image',
            field=models.ImageField(default=b'books/empty_cover.jpg', upload_to=store.models.cover_upload_path),
        ),
    ]
