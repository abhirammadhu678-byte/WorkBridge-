from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_customuser_place'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='location',
        ),
    ]
