from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grounding', '0002_source_edition'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='nickname',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
