from django.db import migrations
import json
import ast

def convert_description_to_json(apps, schema_editor):
    Post = apps.get_model('api', 'Post')
    for post in Post.objects.all():
        desc = post.description
        if desc:
            if isinstance(desc, str):
                try:
                    json.loads(desc)
                    continue
                except Exception:
                    try:
                        parsed = ast.literal_eval(desc)
                        if isinstance(parsed, dict):
                            post.description = parsed
                            post.save(update_fields=['description'])
                            continue
                    except Exception:
                        pass
                    plain_text_raw = {
                        "blocks": [
                            {
                                "key": "plain",
                                "text": desc,
                                "type": "unstyled",
                                "depth": 0,
                                "inlineStyleRanges": [],
                                "entityRanges": [],
                                "data": {}
                            }
                        ],
                        "entityMap": {}
                    }
                    post.description = plain_text_raw
                    post.save(update_fields=['description'])
            elif isinstance(desc, dict):
                continue
            else:
                plain_text_raw = {
                    "blocks": [
                        {
                            "key": "plain",
                            "text": str(desc),
                            "type": "unstyled",
                            "depth": 0,
                            "inlineStyleRanges": [],
                            "entityRanges": [],
                            "data": {}
                        }
                    ],
                    "entityMap": {}
                }
                post.description = plain_text_raw
                post.save(update_fields=['description'])

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_add_otp_and_reset_token_to_user'),
    ]

    operations = [
        migrations.RunPython(convert_description_to_json),
    ]
