from django.db import migrations, models


def set_lock_minutes_to_five(apps, schema_editor):
    ScoringRule = apps.get_model("pool", "ScoringRule")
    ScoringRule.objects.filter(pk=1).update(lock_minutes=5)


def set_lock_minutes_to_fifteen(apps, schema_editor):
    ScoringRule = apps.get_model("pool", "ScoringRule")
    ScoringRule.objects.filter(pk=1).update(lock_minutes=15)


class Migration(migrations.Migration):
    dependencies = [
        ("pool", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="scoringrule",
            name="lock_minutes",
            field=models.PositiveSmallIntegerField(default=5),
        ),
        migrations.RunPython(set_lock_minutes_to_five, set_lock_minutes_to_fifteen),
    ]
