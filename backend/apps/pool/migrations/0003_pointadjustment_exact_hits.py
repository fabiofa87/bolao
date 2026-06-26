from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pool", "0002_lock_minutes_five"),
    ]

    operations = [
        migrations.AddField(
            model_name="pointadjustment",
            name="exact_hits",
            field=models.IntegerField(default=0),
        ),
    ]
