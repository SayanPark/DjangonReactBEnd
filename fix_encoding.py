# fix_encoding.py
import sys

input_file = 'data.json'
output_file = 'data_fixed.json'

with open(input_file, 'rb') as f:
    data = f.read()

# Decode with 'utf-8-sig' to remove BOM if present
text = data.decode('utf-8-sig')

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Fixed encoding saved to {output_file}")
