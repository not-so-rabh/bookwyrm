# Generated by Django 3.2.13 on 2022-07-03 18:42

from django.db import migrations, models
from django.db.models import OuterRef, Subquery, F, Q


# TODO: test this
def set_read_status(apps, schema_editor):
    """Infer the correct reading status from the existing readthrough data"""
    db_alias = schema_editor.connection.alias
    readthrough_model = apps.get_model("bookwyrm", "ReadThrough")

    # if it's "active", it's currenly reading
    # OR if it has a start date but no stop or finish date
    readthrough_model.objects.using(db_alias).filter(
        Q(is_active=True)
        | Q(
            start_date__isnull=False,
            finish_date__isnull=True,
            stopped_date__isnull=True,
        )
    ).update(read_status="reading")

    # if it has finished date, it's read. strictly speaking this is unnecessary if all
    # is well because this is the default value.
    readthrough_model.objects.using(db_alias).filter(
        finished_date__isnull=False
    ).update(read_status="read")

    # if it has a stopped date, it's stopped
    readthrough_model.objects.using(db_alias).filter(stooped_date__isnull=False).update(
        read_status="stopped-reading"
    )

    # no to-read readthroughs currently exist

    # identify books on shelves that don't have statuses and create statuses for them
    # this will be all to-read books, plus any number of others
    shelfbook_model = apps.get_model("bookwyrm", "ShelfBook")

    statuses = readthrough_model.objects.using(db_alias).filter(
        user=OuterRef("shelf__user"),
        book=OuterRef("book"),
        status=OuterRef("shelf__identifier"),
    )
    statusesless_shelfbooks = (
        shelfbook_model.objects.using(db_alias)
        .filter(
            shelf__editable=False,  # on a functional shelf
        )
        .annotate(  # check if this shelbook has an associated status
            status_exists=Subquery(statuses.exists())
        )
    )

    # create new statuses
    readthrough_model.objects.bulk_create(
        [
            readthrough_model(
                read_status=sb.shelf.identifier,
                book=sb.book,
                user=sb.shelf.user,
            )
            for sb in statusesless_shelfbooks.objects.all()
        ]
    )


def merge_finish_stopped_dates(apps, schema_editor):
    """Combine the finished and stopped dates fields"""
    db_alias = schema_editor.connection.alias
    readthrough_model = apps.get_model("bookwyrm", "ReadThrough")
    readthrough_model.objects.using(db_alias).filter(stopped_date__isnull=False).update(
        finish_date=F("stopped_date")
    )


def unmerge_finish_stopped_dates(apps, schema_editor):
    """Combine the finished and stopped dates fields"""
    db_alias = schema_editor.connection.alias
    readthrough_model = apps.get_model("bookwyrm", "ReadThrough")
    readthrough_model.objects.using(db_alias).filter(
        read_status="stopped-reading",
        finish_date__isnull=False,
    ).update(stopped_date=F("finish_date"))


class Migration(migrations.Migration):

    dependencies = [
        ("bookwyrm", "0150_readthrough_stopped_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="readthrough",
            name="read_status",
            field=models.CharField(
                choices=[
                    ("to-read", "To Read"),
                    ("reading", "Currently Reading"),
                    ("read", "Read"),
                    ("stopped-reading", "Stopped Reading"),
                ],
                default="read",
                max_length=20,
            ),
        ),
        migrations.RemoveField(
            model_name="readthrough",
            name="is_active",
        ),
        migrations.RunPython(merge_finish_stopped_dates, unmerge_finish_stopped_dates),
        migrations.RemoveField(
            model_name="readthrough",
            name="stopped_date",
        ),
    ]
