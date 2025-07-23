import sys

input_file = 'backend/data.json'
output_file = 'backend/data_fixed.json'

encodings_to_try = ['utf-8-sig', 'utf-16', 'utf-32']

for enc in encodings_to_try:
    try:
        with open(input_file, 'rb') as f:
            data = f.read()
        text = data.decode(enc)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Successfully decoded with {enc} and saved to {output_file}")
        break
    except UnicodeDecodeError as e:
        print(f"Failed to decode with {enc}: {e}")
else:
    print("Failed to decode the file with tried encodings.")
