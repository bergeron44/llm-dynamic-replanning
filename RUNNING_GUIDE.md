# 🚀 מדריך הרצת הניסויים - כל האפשרויות

## 📝 סקירה כללית

הפרויקט הזה מריץ **סימולציה של רובוט** שנוסע במבוך, מחפש חלב, ומחליט מתי לעצור בחנויות שהוא מגלה.
אתה יכול לשלוט ב-2 פרמטרים עיקריים:
1. **ALGORITHM_MODE** - איך הסוכן "חושב" ומחליט
2. **SCENARIO_ID** - איזה לוח/מבוך/תרחיש הוא רץ עליו

---

## 🎯 תרחישים (SCENARIOS)

יש לך **5 תרחישים שונים**, כל אחד בודק משהו אחר:

### **SCENARIO_1 - "העץ הירושלמי" 🌳**
```bash
SCENARIO_ID=SCENARIO_1
```
- **מה:** עץ עתיק שלא קשור לחלב בכלל
- **אתגר:** בדיקת סינון רעש - האם הסוכן יזהה שזה לא רלוונטי?
- **מיקום:** (3, 2)
- **מחיר:** אין (זה עץ, לא חנות)

**מתי להשתמש:** בדוק אם הסוכן מבזבז זמן על חפצים לא רלוונטיים

---

### **SCENARIO_2 - "קצביית משה" 🥩**
```bash
SCENARIO_ID=SCENARIO_2
```
- **מה:** חנות קצב אמיתית (מוכרת בשר, לא חלב)
- **אתגר:** בדיקת רלוונטיות שגויה - האם הסוכן מבין שקצב לא מוכר חלב?
- **מיקום:** (2, 4)
- **מחיר:** אין (לא מוכר חלב)

**מתי להשתמש:** בדוק אם הסוכן מזהה נכון שזה חנות אבל לא רלוונטית

---

### **SCENARIO_3 - "רמי לוי" 🛒**
```bash
SCENARIO_ID=SCENARIO_3
```
- **מה:** סופר זול (2.5₪) אבל **רחוק יחסית** (דטור של כמה צעדים)
- **אתגר:** בדיקת איזון עלות-מרחק - האם כדאי לנסוע רחוק?
- **מיקום:** (10, 6) - נראה מהמסלול אבל דורש דטור
- **מחיר:** ₪2.5 (זול מאוד)

**מתי להשתמש:** בדוק אם הסוכן יודע לחשב מתי רחוק מדי

---

### **SCENARIO_4 - "מגה בולדוג" (המתוק) 🎯**
```bash
SCENARIO_ID=SCENARIO_4
```
- **מה:** סופר קרוב (2 צעדים) במחיר סביר (₪3.5)
- **אתגר:** התרחיש "המתוק" - כל סוכן חכם צריך לעצור כאן
- **מיקום:** (3, 3) - קרוב מאוד
- **מחיר:** ₪3.5 (זול מהמחיר ב-victory: ₪4.0)

**מתי להשתמש:** בדוק אם הסוכן מזהה הזדמנות טובה

---

### **SCENARIO_5 - "AM:PM Express" (המלכודת) 💸**
```bash
SCENARIO_ID=SCENARIO_5
```
- **מה:** חנות נוחות **יקרה מאוד** (₪12) אבל קרובה (5 צעדים)
- **אתגר:** בדיקת "מלכודת" - האם הסוכן יודע להתעלם ממשהו קרוב אבל יקר?
- **מיקום:** (6, 4)
- **מחיר:** ₪12.0 (יקר פי 3!)

**מתי להשתמש:** בדוק אם הסוכן לא מתפתה למשהו קרוב אבל יקר מדי

---

## 🤖 אלגוריתמים (ALGORITHM_MODE)

יש לך **4 אלגוריתמים שונים**, כל אחד מייצג "אישיות" אחרת של הסוכן:

### **ALGORITHM A - "העיוור" 👤**
```bash
ALGORITHM_MODE=A
```
- **מה עושה:** **מתעלם מכל תגלית** - פשוט הולך ישר ליעד
- **איך:** לא עושה replan אף פעם, רק הולך מההתחלה לסוף
- **מתי טוב:** Baseline - בודק מה המחיר בלי שום אופטימיזציה
- **מתי גרוע:** מפספס כל הזדמנות

**דוגמה:**
```
סוכן: "ראיתי מגה בולדוג? לא אכפת לי, אני ממשיך ל-victory"
תוצאה: משלם ₪4.0 במקום ₪3.5
```

---

### **ALGORITHM B - "הטיפש" 🤡**
```bash
ALGORITHM_MODE=B
```
- **מה עושה:** **עוצר ומתכנן מחדש** על כל תגלית, **בלי לבדוק מה זה**
- **איך:** כל פעם שהוא רואה משהו, מוסיף אותו ל-PDDL ומתכנן מחדש
- **מתי טוב:** ניצול מקסימלי של הזדמנויות (אם יש)
- **מתי גרוע:** מבזבז זמן על עצים, קצבים, וכל דבר לא רלוונטי

**דוגמה:**
```
סוכן: "ראיתי עץ? בואו נעצור ונבדוק אם הוא מוכר חלב!"
תוצאה: עוצר על כל דבר, אפילו עץ עתיק
```

---

### **ALGORITHM C - "החכם" (מומלץ!) 🧠**
```bash
ALGORITHM_MODE=C
```
- **מה עושה:** **שואל LLM (Gemini)** מה זה ומה לעשות
- **איך:**
  1. שואל את LLM מה זה החפץ שגילה
  2. שואל את LLM אם כדאי לעצור
  3. מחליט בצורה אסטרטגית
- **מתי טוב:** מתעלם מרעש, מנצל הזדמנויות אמיתיות
- **מתי גרוע:** יותר איטי (קריאות ל-API)

**דוגמה:**
```
סוכן: "ראיתי מגה בולדוג? בואו אשאל את LLM..."
LLM: "זה סופר שמוכר חלב במחיר ₪3.5, קרוב מאוד - כדאי לעצור!"
סוכן: "בסדר, אני עוצר!"
```

---

### **ALGORITHM D - "המתמטי" 📊**
```bash
ALGORITHM_MODE=D
```
- **מה עושה:** **נוסחה מתמטית פשוטה** - לא צריך LLM
- **הנוסחה:** `עצור אם (חיסכון > ₪1) AND (מרחק < 10 צעדים)`
- **איך:**
  1. בודק אם זה חנות חלב (עם LLM)
  2. אם כן, מחשב: חיסכון = ₪4.0 - מחיר_החנות
  3. בודק את הנוסחה
- **מתי טוב:** מהיר, אובייקטיבי, עובד טוב
- **מתי גרוע:** פחות "חכם" מ-Algorithm C

**דוגמה:**
```
סוכן: "רמי לוי - חיסכון ₪1.5, מרחק 20 צעדים"
נוסחה: "1.5 > 1 ✅ אבל 20 < 10 ❌"
תוצאה: "לא כדאי - רחוק מדי"
```

---

## 🎮 דוגמאות הרצה

### הרצה בסיסית (ברירת מחדל):
```bash
python run_live_dashboard.py
```
**זה מריץ:** Algorithm C + SCENARIO_4

---

### הרצה מותאמת:
```bash
ALGORITHM_MODE=C SCENARIO_ID=SCENARIO_1 python run_live_dashboard.py
```
**זה מריץ:** הסוכן החכם (C) על התרחיש עם העץ

---

### כל השילובים האפשריים:

```bash
# Algorithm A (עיוור)
ALGORITHM_MODE=A SCENARIO_ID=SCENARIO_1 python run_live_dashboard.py
ALGORITHM_MODE=A SCENARIO_ID=SCENARIO_2 python run_live_dashboard.py
ALGORITHM_MODE=A SCENARIO_ID=SCENARIO_3 python run_live_dashboard.py
ALGORITHM_MODE=A SCENARIO_ID=SCENARIO_4 python run_live_dashboard.py
ALGORITHM_MODE=A SCENARIO_ID=SCENARIO_5 python run_live_dashboard.py

# Algorithm B (טיפש)
ALGORITHM_MODE=B SCENARIO_ID=SCENARIO_1 python run_live_dashboard.py
ALGORITHM_MODE=B SCENARIO_ID=SCENARIO_2 python run_live_dashboard.py
ALGORITHM_MODE=B SCENARIO_ID=SCENARIO_3 python run_live_dashboard.py
ALGORITHM_MODE=B SCENARIO_ID=SCENARIO_4 python run_live_dashboard.py
ALGORITHM_MODE=B SCENARIO_ID=SCENARIO_5 python run_live_dashboard.py

# Algorithm C (חכם) - מומלץ!
ALGORITHM_MODE=C SCENARIO_ID=SCENARIO_1 python run_live_dashboard.py
ALGORITHM_MODE=C SCENARIO_ID=SCENARIO_2 python run_live_dashboard.py
ALGORITHM_MODE=C SCENARIO_ID=SCENARIO_3 python run_live_dashboard.py
ALGORITHM_MODE=C SCENARIO_ID=SCENARIO_4 python run_live_dashboard.py
ALGORITHM_MODE=C SCENARIO_ID=SCENARIO_5 python run_live_dashboard.py

# Algorithm D (מתמטי)
ALGORITHM_MODE=D SCENARIO_ID=SCENARIO_1 python run_live_dashboard.py
ALGORITHM_MODE=D SCENARIO_ID=SCENARIO_2 python run_live_dashboard.py
ALGORITHM_MODE=D SCENARIO_ID=SCENARIO_3 python run_live_dashboard.py
ALGORITHM_MODE=D SCENARIO_ID=SCENARIO_4 python run_live_dashboard.py
ALGORITHM_MODE=D SCENARIO_ID=SCENARIO_5 python run_live_dashboard.py
```

**סה"כ: 20 שילובים אפשריים! (4 אלגוריתמים × 5 תרחישים)**

---

## 📊 הרצת כל הניסויים בבת אחת

### הרצה אוטומטית של כל השילובים:
```bash
./run_batch_experiments.sh
```
**זה מריץ:** כל 16 השילובים (SCENARIO_1-4 × Algorithms A-D) עם seeds קבועים

---

### הרצת אלגוריתם בודד על כל התרחישים:
```bash
python run_single_algorithm.py
```
**אז תבחר:** A, B, C, או D
**זה יריץ:** האלגוריתם שבחרת על כל התרחישים

---

## 🎯 מה לבדוק בכל תרחיש

### SCENARIO_1 (עץ):
- ✅ **Algorithm A:** צריך להתעלם (בסדר)
- ✅ **Algorithm B:** צריך להתעלם (אבל עוצר - בזבוז זמן)
- ✅ **Algorithm C:** צריך להתעלם (LLM מזהה שזה עץ)
- ✅ **Algorithm D:** צריך להתעלם (לא מוכר חלב)

### SCENARIO_2 (קצב):
- ✅ **Algorithm A:** צריך להתעלם (בסדר)
- ✅ **Algorithm B:** צריך להתעלם (אבל עוצר - בזבוז)
- ✅ **Algorithm C:** צריך להתעלם (LLM מזהה שקצב לא מוכר חלב)
- ✅ **Algorithm D:** צריך להתעלם (לא מוכר חלב)

### SCENARIO_3 (רמי לוי רחוק):
- ⚠️ **Algorithm A:** מפספס (לא עוצר)
- ❌ **Algorithm B:** עוצר (בזבוז - רחוק מדי)
- ✅ **Algorithm C:** אמור לבדוק ולאפשר (LLM מחליט)
- ⚠️ **Algorithm D:** לא עוצר (מרחק > 10)

### SCENARIO_4 (מגה בולדוג - המתוק):
- ❌ **Algorithm A:** מפספס הזדמנות (לא עוצר)
- ✅ **Algorithm B:** עוצר (טוב, אבל גם על כל דבר אחר)
- ✅ **Algorithm C:** עוצר (LLM מזהה הזדמנות)
- ✅ **Algorithm D:** עוצר (חיסכון > 1, מרחק < 10)

### SCENARIO_5 (AM:PM יקר):
- ✅ **Algorithm A:** ממשיך (בסדר)
- ❌ **Algorithm B:** עוצר (טעות - יקר מדי)
- ✅ **Algorithm C:** לא עוצר (LLM מזהה שמחיר גבוה)
- ✅ **Algorithm D:** לא עוצר (חיסכון < 0)

---

## 🔍 מה הקומנד שלך עושה:

```bash
ALGORITHM_MODE=C SCENARIO_ID=SCENARIO_1 python run_live_dashboard.py
```

**זה אומר:**
1. **ALGORITHM_MODE=C** - הסוכן החכם (שואל LLM)
2. **SCENARIO_ID=SCENARIO_1** - התרחיש עם העץ הירושלמי
3. **python run_live_dashboard.py** - הרצת הסימולציה

**מה יקרה:**
- הסוכן יתחיל ב-(1, 1)
- יעבור דרך המבוך לכיוון (18, 18)
- כשהוא יגיע ל-(10, 10) הוא יגלה עץ
- הוא ישאל את LLM מה זה
- LLM יגיד "זה עץ עתיק, לא חנות"
- הסוכן ימשיך ישר (לא יעצור)

---

## 📁 קבצי תוצאות

לאחר ההרצה, התוצאות נשמרות ב:

- **`experiment_results.csv`** - כל התוצאות בטבלה
- **`trace.log`** - לוג מפורט של מה קרה
- **גרפים:** אם תריץ `generate_experiment_graphs.py`

---

## 💡 טיפים

1. **התחל עם:** `ALGORITHM_MODE=C SCENARIO_ID=SCENARIO_4` - זה התרחיש הכי פשוט
2. **בדוק את הלוגים:** `trace.log` מכיל המון מידע על מה קרה
3. **השווה תוצאות:** ריץ אותו תרחיש עם אלגוריתמים שונים ותראה את ההבדל
4. **שתמש ב-seed:** אם תריץ עם אותו seed, תקבל אותו לוח בדיוק

---

## 🐛 בעיות נפוצות

### הסוכן תקוע בלולאה אינסופית?
- **פתרון:** זה אומר שיש בעיה ב-PDDL או בתכנון
- **בדוק:** `trace.log` יראה מה קרה

### LLM לא עובד?
- **בדוק:** יש לך API key ב-`.env`?
- **בדוק:** יש לך חיבור לאינטרנט?

### הסוכן לא עוצר על חנות?
- **בדוק:** מה ALGORITHM_MODE? (A לא עוצר אף פעם)
- **בדוק:** מה התרחיש? (SCENARIO_1 זה עץ, לא חנות)

---

## 📞 עזרה

אם משהו לא עובד, בדוק את `trace.log` - יש שם המון מידע על מה קרה בכל צעד!






