from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0005_alter_jobapplication_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='customer',
            field=models.ForeignKey(
                null=True,
                limit_choices_to={'user_type': 'customer'},
                on_delete=django.db.models.deletion.CASCADE,
                related_name='posted_jobs',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]