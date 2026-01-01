# ניתוח: לולאה אינסופית עם obstacles

## הבעיה
הסוכן נכנס ללולאה אינסופית כשהוא מנסה להיכנס לחנות שאינה "allowed store".

## סדר האירועים

### 1. גילוי האובייקט (שורה 182-192 בלוג)
- **אובייקט**: `burger_ranch_hod_hasharon` ב-`(3, 8)`
- **Algorithm B**: מפעיל `reasoner.analyze_observation("burger_ranch_hod_hasharon")`
- **תוצאה**: `sells_milk=False` (זה מסעדה, לא סופר)
- **סיווג**: `obj_type = 'obstacle'` (לא 'store')
- **חסימת נתיב**: `is_blocking = True`
- **החלטה**: `reason='obstacle_blocking_path'`, `metadata={'type': 'obstacle', 'blocks_path': True}`

### 2. עדכון state_manager (שורה 1282, 1289-1297 בקוד)
- `new_discovery.update(decision['metadata'])` מעדכן את `new_discovery` עם `type='obstacle'`
- `state_manager.add_discovery(..., obj_type='obstacle', ...)` מוסיף את האובייקט
- **תוצאה**: האובייקט ב-`discovered_objects` עם `type='obstacle'` (לא 'store')

### 3. עדכון PDDL (שורה 1327-1330 בקוד)
- **בעיה**: `patcher.inject_dynamic_state(current_predicates)` נקרא
- `inject_dynamic_state` לא מסמן obstacles כ-`(blocked loc_x_y)` ב-PDDL!
- **תוצאה**: הפלנר לא יודע ש-`loc_3_8` חסום

### 4. תכנון מחדש (שורה 1339)
- הפלנר רץ אבל לא יודע ש-`loc_3_8` חסום
- התוכנית כוללת `drive loc_2_8 loc_3_8` למרות שהמיקום חסום

### 5. ביצוע התוכנית (שורה 236-259 בלוג)
- הסוכן מנסה לנוע ל-`(3, 8)`
- הקוד מזהה שזה store (שורה 236: "Object type: ball - This is our destination per plan")
- הבדיקה: `is_allowed_store = False` כי האובייקט עם `type='obstacle'` (לא 'store')
- הקוד חוסם את הכניסה (שורה 238: "🚫 Blocked: Cannot enter store at (3, 8)")
- הסוכן נשאר ב-`(2, 8)` → מופעל replan שוב → **לולאה אינסופית**

## הבעיה העיקרית

**בשורה 1330 בקוד**: משתמשים ב-`inject_dynamic_state` במקום `update_problem_file`

- `inject_dynamic_state` לא מסמן obstacles כ-`(blocked loc_x_y)` ב-PDDL
- `update_problem_file` כן מסמן obstacles כ-`(blocked loc_x_y)` (שורה 270-272 ב-pddl_patcher.py)

## הפתרון

צריך להחליף את `patcher.inject_dynamic_state(current_predicates)` ב-`patcher.update_problem_file(env.agent_pos, state_manager.discovered_objects)` בשורה 1330.

