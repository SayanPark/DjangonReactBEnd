import os
import django
import json
import ast
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Post

def clean_description_data():
    posts = Post.objects.all()
    for post in posts:
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
                            post.description = json.dumps(parsed, ensure_ascii=False)
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
                    post.description = json.dumps(plain_text_raw, ensure_ascii=False)
                    post.save(update_fields=['description'])
            elif isinstance(desc, dict):
                post.description = json.dumps(desc, ensure_ascii=False)
                post.save(update_fields=['description'])
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
                post.description = json.dumps(plain_text_raw, ensure_ascii=False)
                post.save(update_fields=['description'])

if __name__ == "__main__":
    clean_description_data()
    print("Description data cleaning completed.")
