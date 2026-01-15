import os

print("🕵️‍♂️ Searching for Fast Downward binary...")

# חיפוש עמוק של הקובץ הקריטי
found = False
for root, dirs, files in os.walk("."):
    if "downward" in root and "release" in root and "downward" in files:
        full_path = os.path.join(root, "downward")
        print(f"\n✅ FOUND BINARY AT: {os.path.abspath(full_path)}")
        found = True

    if "fast-downward.py" in files:
        print(f"ℹ️  Driver script found at: {os.path.abspath(os.path.join(root, 'fast-downward.py'))}")

if not found:
    print("\n❌ Could not find the compiled binary 'downward'.")
    print("This confirms the build is missing or deleted.")
    print("Check inside 'downward/builds/release/bin/' manually.")
else:
    print("\n💡 TIP: Make sure you run the script from the correct root directory!")








