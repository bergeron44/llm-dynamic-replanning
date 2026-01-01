# תיקון: מניעת מעבר דרך חנויות שלא צריך

## 🔴 הבעיה

המנגנון "Forcing physical entry" (שורה 1581) מופעל על **כל** חנות שהתכנית מכוונת אליה, לא רק על:
1. Victory store (המטרה הסופית)
2. חנויות שהסוכן החליט להיכנס אליהן (replan)

זה גורם לסוכן לעבור דרך חנויות שהוא לא צריך להיכנס אליהן.

---

## 🔧 התיקון

**מיקום**: שורה 1580, לפני `if intended_pos == planned_target_pos_for_override:`

**קוד נוכחי** (שורות 1577-1581):
```python
                        intended_pos = (prev_pos[0] + dx, prev_pos[1] + dy)
                        
                        # If we are facing the target, FORCE the move
                        if intended_pos == planned_target_pos_for_override:
                            logger.info("PHYSICS", f"🛡️ Forcing physical entry onto Goal Object at {intended_pos}")
```

**קוד מתוקן**:
```python
                        intended_pos = (prev_pos[0] + dx, prev_pos[1] + dy)
                        
                        # Check if this is a store we're allowed to enter:
                        # 1. Victory store (goal) - always allowed
                        # 2. Store we decided to visit (in discovered_objects with type='store')
                        is_victory_store = (intended_pos == victory_pos)
                        is_allowed_store = False
                        
                        # Check if it's a discovered store we're planning to visit
                        # (Only stores we decided to visit are in discovered_objects)
                        for obj_name, obj_data in state_manager.discovered_objects.items():
                            if obj_data.get('type') == 'store' and 'pos' in obj_data:
                                if tuple(obj_data['pos']) == intended_pos:
                                    # This is a store we discovered and decided to visit (replan)
                                    is_allowed_store = True
                                    break
                        
                        # Only force entry if it's victory store OR an allowed store
                        if intended_pos == planned_target_pos_for_override and (is_victory_store or is_allowed_store):
                            store_type = 'Victory Store' if is_victory_store else 'Allowed Store'
                            logger.info("PHYSICS", f"🛡️ Forcing physical entry onto {store_type} at {intended_pos}")
                            # Manually set agent position (teleport on top of ball/victory)
                            if isinstance(env.agent_pos, np.ndarray):
                                env.agent_pos = np.array([intended_pos[0], intended_pos[1]])
                            else:
                                env.agent_pos = list(intended_pos) if isinstance(env.agent_pos, list) else intended_pos
                            logger.info("PHYSICS", f"✅ Agent position manually set to {env.agent_pos}")
                        elif intended_pos == planned_target_pos_for_override:
                            # This is a store we're NOT allowed to enter - treat as blocked
                            logger.warning("PHYSICS", f"🚫 Blocked: Cannot enter store at {intended_pos} (not victory and not in allowed stores)")
                            # Don't force entry - let physics handle it (will trigger replan)
```

---

## 📋 הסבר

התיקון מוסיף בדיקה:
1. **is_victory_store**: האם זה victory store (המטרה הסופית)
2. **is_allowed_store**: האם זה חנות שהסוכן גילה והחליט להיכנס אליה (נמצאת ב-`state_manager.discovered_objects` עם `type='store'`)

רק אם אחד מהתנאים מתקיים, המנגנון "Forcing physical entry" מופעל.

אם זה חנות שלא מותרת, הסוכן לא יעבור דרכה, וזה יגרום ל-replan.

---

## ✅ תוצאה

לאחר התיקון:
- ✅ הסוכן יעבור דרך victory store (כמו שצריך)
- ✅ הסוכן יעבור דרך חנויות שהחליט להיכנס אליהן (replan)
- ❌ הסוכן **לא** יעבור דרך חנויות אחרות (יחסם ויעשה replan)

