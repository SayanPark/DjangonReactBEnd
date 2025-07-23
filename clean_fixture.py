import json

def clean_fixture(input_file='data_clean_utf8.json', output_file='data_clean_no_user_permissions.json'):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cleaned_data = []
    for entry in data:
        # Remove user_permissions field from api.user model entries
        if entry.get('model') == 'api.user':
            fields = entry.get('fields', {})
            if 'user_permissions' in fields:
                del fields['user_permissions']
            cleaned_data.append(entry)
        # Remove entries related to user permissions (auth.permission) if any
        elif entry.get('model') == 'auth.permission':
            continue
        else:
            cleaned_data.append(entry)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2)

    print(f"Cleaned fixture saved to {output_file}")

if __name__ == '__main__':
    clean_fixture()
