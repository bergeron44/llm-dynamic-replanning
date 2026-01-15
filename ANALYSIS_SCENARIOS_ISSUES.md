# 🔍 ניתוח בעיות בתרחישים (Scenarios)

## 📋 סקירה כללית

הפרויקט כולל **5 תרחישים** (SCENARIO_1 עד SCENARIO_5) שבודקים מיכרים שונים, אבל יש מספר בעיות ביישום שלהם.

---

## ❌ הבעיות שזוהו

### **בעיה #1: SCENARIO_5 לא כלול ב-`run_single_algorithm.py`**

**מיקום:** `run_single_algorithm.py`, שורה 77

**הבעיה:**
```python
scenarios = ['SCENARIO_1', 'SCENARIO_2', 'SCENARIO_3', 'SCENARIO_4']  # ❌ חסר SCENARIO_5!
```

**השפעה:**
- כשמריצים `run_single_algorithm.py`, התרחיש החמישי (SCENARIO_5 - "The Expensive Trap") לא נרץ
- זה מונע בדיקה של מקרה שבו חנות יקרה וקרובה (צריכה להידחות)

**פתרון:** להוסיף SCENARIO_5 לרשימה:
```python
scenarios = ['SCENARIO_1', 'SCENARIO_2', 'SCENARIO_3', 'SCENARIO_4', 'SCENARIO_5']
```

**גם צריך להוסיף seed:**
```python
seeds = {
    'SCENARIO_1': 12345,
    'SCENARIO_2': 23456,
    'SCENARIO_3': 34567,
    'SCENARIO_4': 45678,
    'SCENARIO_5': 56789  # ❌ חסר!
}
```

---

### **בעיה #2: `am_pm_express` לא נמצא ב-`stores_database.py`**

**מיקום:** `scenarios.py`, שורה 69 | `stores_database.py` - לא קיים

**הבעיה:**
- SCENARIO_5 משתמש ב-`am_pm_express` כחנוית הניסיון
- אבל `am_pm_express` **לא נמצא** ב-`stores_database.py`
- זה יכול לגרום לבעיות כשה-LLM מנסה לנתח את האובייקט

**השפעה:**
- כשה-LLM מנתח את `am_pm_express`, הוא לא יכול למצוא אותו במסד הנתונים
- זה יכול לגרום להתנהגות לא צפויה (LLM צריך לנחש או להשתמש בידע כללי)

**פתרון:** להוסיף `am_pm_express` ל-`stores_database.py`:
```python
"am_pm_express": {
    "type": "convenience_store",
    "sells_milk": True,  # AM:PM מוכר חלב
    "category": "convenience",
    "description": "AM:PM Express convenience store - very expensive",
    "address": "Various locations",
    "city": "Israel",
    "price_estimate": 12.0,  # יקר מאוד! (3x מחיר Victory)
    "color": "yellow",
    "real_info": "24/7 convenience store chain, known for high prices on convenience items"
}
```

---

### **בעיה #3: SCENARIO_5 משתמש ב-victory_pos שונה (10, 10) במקום (18, 18)**

**מיקום:** `scenarios.py`, שורה 67

**הבעיה:**
```python
"SCENARIO_5": {
    ...
    "victory_pos": (10, 10),  # ⚠️ שונה מכל התרחישים האחרים (18, 18)
    ...
}
```

**השפעה:**
- כל התרחישים האחרים משתמשים ב-victory_pos = (18, 18)
- SCENARIO_5 משתמש ב-(10, 10) כדי להפוך את המלכודת למפתה יותר
- זה בסדר מבחינת הלוגיקה, אבל יכול לגרום לבלבול בניתוח התוצאות

**הערה:** זה **לא באג**, אלא החלטה עיצובית - אבל צריך להיות מודעים לזה בעת ניתוח תוצאות.

---

## ✅ מה כן עובד טוב

### **1. כל התרחישים משתמשים באותו planner חיצוני**

**מיקום:** `run_live_dashboard.py`

**אימות:**
- כל התרחישים עוברים דרך `run_live_dashboard.py`
- משתמשים ב-`FastDownwardRunner` (planner חיצוני)
- אותו לוגיקה של תכנון PDDL

**קוד רלוונטי:**
```python
runner = FastDownwardRunner(env=env)
current_plan = runner.run_planner("domain.pddl", "problem_initial.pddl")
```

✅ **זה עובד כמו שצריך!**

---

### **2. כל התרחישים משתמשים באותם 4 אלגוריתמים**

**מיקום:** `run_live_dashboard.py`, שורה 661

**אימות:**
- כל התרחישים מקבלים `ALGORITHM_MODE` מה-environment variable
- אותו dispatcher (should_replan_for_discovery) מטפל בכל התרחישים
- 4 האלגוריתמים (A/B/C/D) עובדים באותה צורה בכל התרחישים

**קוד רלוונטי:**
```python
ALGORITHM_MODE = os.environ.get('ALGORITHM_MODE', 'C').upper()  # A/B/C/D
decision = should_replan_for_discovery(
    new_discovery=new_discovery,
    current_plan=current_plan,
    current_step_index=current_step_index,
    algorithm_mode=ALGORITHM_MODE,  # ✅ אותו אלגוריתם
    reasoner=reasoner,
    state_manager=state_manager,
    env=env
)
```

✅ **זה עובד כמו שצריך!**

---

### **3. תרחישים עם אובייקטים שלא מוכרים חלב מטופלים נכון**

**דוגמאות:** SCENARIO_1 (עץ), SCENARIO_2 (קצב)

**אימות:**
- SCENARIO_1: `old_tree_jerusalem_forest` נמצא ב-`stores_database.py` עם `sells_milk: False`
- SCENARIO_2: `moshe_butcher_rehovot` נמצא ב-`stores_database.py` עם `sells_milk: False`
- ה-LLM Reasoner יכול לנתח אותם נכון ולהחליט שהם לא רלוונטיים

**קוד רלוונטי:**
```python
analysis = reasoner.analyze_observation(discovery_name)
if analysis.get('sells_milk', False):
    # רק אם מוכר חלב - מתכנן מחדש
    ...
else:
    # לא מוכר חלב - ממשיך בתכנית המקורית
    ...
```

✅ **זה עובד כמו שצריך!**

---

## 📊 סיכום הבעיות

| בעיה | מיקום | חומרה | סטטוס |
|------|-------|--------|-------|
| SCENARIO_5 חסר ב-`run_single_algorithm.py` | `run_single_algorithm.py:77` | ⚠️ בינוני | ❌ לא תוקן |
| `am_pm_express` חסר ב-`stores_database.py` | `stores_database.py` | ⚠️ בינוני | ❌ לא תוקן |
| SCENARIO_5 עם victory_pos שונה | `scenarios.py:67` | ℹ️ מידע | ✅ זה בסדר (החלטה עיצובית) |

---

## 🛠️ המלצות לתיקון

### **תיקון #1: להוסיף SCENARIO_5 ל-`run_single_algorithm.py`**

```python
# שורה 17-22
seeds = {
    'SCENARIO_1': 12345,
    'SCENARIO_2': 23456,
    'SCENARIO_3': 34567,
    'SCENARIO_4': 45678,
    'SCENARIO_5': 56789  # ✅ להוסיף
}

# שורה 77
scenarios = ['SCENARIO_1', 'SCENARIO_2', 'SCENARIO_3', 'SCENARIO_4', 'SCENARIO_5']  # ✅ להוסיף
```

### **תיקון #2: להוסיף `am_pm_express` ל-`stores_database.py`**

```python
"am_pm_express": {
    "type": "convenience_store",
    "sells_milk": True,
    "category": "convenience",
    "description": "AM:PM Express convenience store - very expensive",
    "address": "Various locations",
    "city": "Israel",
    "price_estimate": 12.0,
    "color": "yellow",
    "real_info": "24/7 convenience store chain, known for high prices on convenience items"
}
```

---

## ✅ מה עובד נכון

1. ✅ כל התרחישים משתמשים באותו planner חיצוני (FastDownward)
2. ✅ כל התרחישים משתמשים באותו אלגוריתם (A/B/C/D) דרך אותו dispatcher
3. ✅ תרחישים עם אובייקטים שלא מוכרים חלב מטופלים נכון
4. ✅ האינטגרציה עם `custom_env.py` עובדת נכון
5. ✅ האינטגרציה עם `run_live_dashboard.py` עובדת נכון

---

## 📝 הערות נוספות

1. **SCENARIO_5 עם victory_pos שונה** - זה החלטה עיצובית כדי להפוך את המלכודת למפתה יותר, אבל צריך להיות מודעים לזה בעת ניתוח תוצאות.

2. **תרחישים שלא נבדקים** - אם `run_single_algorithm.py` לא כולל את SCENARIO_5, זה אומר שהוא לא נבדק באופן אוטומטי, מה שעלול להוביל לכך שמקרי קצה לא נבדקים.

3. **מסד הנתונים לא שלם** - אם `am_pm_express` לא נמצא במסד הנתונים, ה-LLM צריך לנחש או להשתמש בידע כללי, מה שעלול להוביל לתוצאות פחות מדויקות.
