import subprocess
import os

def dumpdata_utf8_clean():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        ['python', 'manage.py', 'dumpdata', '--exclude', 'auth.permission', '--exclude', 'contenttypes', '--exclude', 'admin.logentry', '--indent', '2'],
        capture_output=True,
        text=True,
        env=env
    )
    if result.returncode != 0:
        print("Error running dumpdata:", result.stderr)
        return
    with open('data_clean_utf8.json', 'w', encoding='utf-8') as f:
        f.write(result.stdout)
    print("Dumpdata output saved to data_clean_utf8.json")

if __name__ == '__main__':
    dumpdata_utf8_clean()