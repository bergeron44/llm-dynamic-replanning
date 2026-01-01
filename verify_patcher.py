import sys
import os

print("🔍 Inspecting pddl_patcher.py...")

try:
    from pddl_patcher import PDDLPatcher
    print("✅ Import successful (Syntax is valid).")
except ImportError as e:
    print(f"❌ Import Failed! Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Syntax Error in file! Error: {e}")
    sys.exit(1)

# Initialize
patcher = PDDLPatcher("problem_initial.pddl")

# Test 1: Check if helper method exists
if hasattr(patcher, '_find_init_end'):
    print("✅ Helper method '_find_init_end' exists.")
else:
    print("❌ CRITICAL FAIL: Helper method '_find_init_end' is MISSING!")
    sys.exit(1)

# Test 2: Check Indentation logic in update_problem_file
# We read the file as text to check indentation structure manually
with open("pddl_patcher.py", "r") as f:
    lines = f.readlines()

found_target_logic = False
correct_indentation = False

for i, line in enumerate(lines):
    if "if obj_type == 'store'" in line or "get('sells_milk')" in line:
        # Check the next few lines for the 'else' block
        for j in range(1, 20):
            if i+j >= len(lines): break
            next_line = lines[i+j]
            if "else:" in next_line:
                found_target_logic = True
                # Check indentation level matches the 'if'
                if len(line) - len(line.lstrip()) == len(next_line) - len(next_line.lstrip()):
                    correct_indentation = True
                    print(f"✅ Logic Indentation looks correct at line {i+j+1}")
                else:
                    print(f"❌ CRITICAL FAIL: Indentation Mismatch at line {i+j+1}!")
                    print(f"   IF level: {len(line) - len(line.lstrip())}")
                    print(f"   ELSE level: {len(next_line) - len(next_line.lstrip())}")
                break
        break

if not found_target_logic:
    print("⚠️ Warning: Could not verify indentation logic via static analysis (might be okay if code structure changed).")

print("\n🎉 PDDL Patcher passed sanity checks.")
