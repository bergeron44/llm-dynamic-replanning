import os

# הנתיב שהקוד שלך מחפש (לפי הלוגים)
expected_path = os.path.abspath("./downward/fast-downward.py")
build_path = os.path.abspath("./downward/builds/release/bin/translate/translate.py")

print(f"Checking paths from: {os.getcwd()}")
print(f"1. Script path: {expected_path} -> {'✅ FOUND' if os.path.exists(expected_path) else '❌ MISSING'}")
print(f"2. Build path:  {build_path} -> {'✅ FOUND' if os.path.exists(build_path) else '❌ MISSING'}")




