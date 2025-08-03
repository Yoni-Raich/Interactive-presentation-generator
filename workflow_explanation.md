# הסבר מפורט על progress_callback ו-workflow.py

## מה זה progress_callback?

ה-`progress_callback` הוא פונקציה שמאפשרת לך לקבל עדכונים בזמן אמת על התקדמות יצירת המצגת. זה עובד כמו "התקשרות חזרה" - המערכת מתקשרת אליך כדי לעדכן אותך על מה שקורה.

### איך זה עובד:

1. **הגדרת הפונקציה**: אתה יוצר פונקציה שמקבלת אובייקט `WorkflowProgress`
2. **העברת הפונקציה**: אתה מעביר את הפונקציה ל-`generate()` או ל-`set_progress_callback()`
3. **קבלת עדכונים**: המערכת קוראת לפונקציה שלך בכל שלב

### דוגמה פשוטה:

```python
def my_progress_callback(progress):
    print(f"שלב נוכחי: {progress.current_step}")
    print(f"התקדמות: {progress.progress_percentage:.1f}%")
    print(f"זמן שעבר: {progress.elapsed_time:.1f} שניות")

# שימוש
generator = PresentationGenerator(config)
result = generator.generate(
    "מדריך פייתון בסיסי", 
    progress_callback=my_progress_callback
)
```

## מה זה workflow.py ולמה צריך אותו?

קובץ ה-`workflow.py` הוא המנהל הראשי של כל תהליך יצירת המצגת. הוא כמו "מנצח התזמורת" שמתאם בין כל הרכיבים השונים.

### התפקידים העיקריים:

#### 1. **ניהול שלבים (Step Management)**
המערכת מחלקת את התהליך ל-5 שלבים עיקריים:
- **content_generation**: יצירת תוכן השקפים עם AI
- **image_generation**: המרת השקפים לתמונות
- **audio_generation**: יצירת קריינות (אם מופעל)
- **video_assembly**: הרכבת הווידאו הסופי (אם מופעל)
- **finalization**: סיום ועיבוד הקבצים

#### 2. **מעקב התקדמות (Progress Tracking)**
```python
@dataclass
class WorkflowProgress:
    current_step: str                    # השלב הנוכחי
    completed_steps: List[str]           # שלבים שהושלמו
    failed_steps: List[str]              # שלבים שנכשלו
    total_steps: int                     # סך השלבים
    start_time: Optional[datetime]       # זמן התחלה
    
    @property
    def progress_percentage(self) -> float:
        # חישוב אחוז ההתקדמות
        return (len(self.completed_steps) / self.total_steps) * 100
```

#### 3. **ניהול משאבים (Resource Management)**
המערכת יוצרת קבצים זמניים ומנהלת אותם:
```python
class ResourceManager:
    def create_temp_dir(self, prefix: str) -> Path:
        # יוצר תיקייה זמנית
    
    def cleanup_all(self) -> None:
        # מנקה את כל הקבצים הזמניים
```

#### 4. **טיפול בשגיאות (Error Handling)**
המערכת מטפלת בשגיאות בכל שלב ומנסה להמשיך או לנקות:
```python
def _execute_step_with_error_handling(self, step_name, step_function, required=True):
    try:
        result = step_function()
        # מסמן שהשלב הצליח
        self._mark_step_complete(step_name)
        return result
    except Exception as e:
        # מטפל בשגיאה ומחליט אם להמשיך או לעצור
        if required:
            raise WorkflowError(f"שלב חובה נכשל: {e}")
```

#### 5. **עיבוד מקבילי (Parallel Processing)**
המערכת מעבדת מספר שקפים במקביל לשיפור ביצועים:
```python
with ThreadPoolExecutor(max_workers=min(4, len(slides))) as executor:
    futures = []
    for slide in slides:
        future = executor.submit(process_slide, slide)
        futures.append(future)
```

### למה צריך את זה?

1. **ארגון**: במקום קוד מבולגן, יש מבנה ברור של שלבים
2. **מעקב**: אתה יודע בדיוק איפה התהליך נמצא
3. **שגיאות**: אם משהו נכשל, אתה יודע בדיוק איפה ומה
4. **ביצועים**: עיבוד מקבילי מזרז את התהליך
5. **ניקיון**: המערכת מנקה אחריה קבצים זמניים
6. **גמישות**: אפשר להוסיף או להסיר שלבים בקלות

### דוגמה מעשית:

```python
def detailed_progress_callback(progress):
    print(f"🔄 {progress.current_step}")
    print(f"📊 התקדמות: {progress.progress_percentage:.1f}%")
    print(f"✅ הושלמו: {len(progress.completed_steps)} מתוך {progress.total_steps}")
    print(f"⏱️ זמן שעבר: {progress.elapsed_time:.1f} שניות")
    
    if progress.failed_steps:
        print(f"❌ שלבים שנכשלו: {progress.failed_steps}")
    
    print("-" * 50)

# שימוש
generator = PresentationGenerator(config)
result = generator.generate(
    "מדריך פייתון למתחילים",
    progress_callback=detailed_progress_callback
)
```

זה יתן לך פלט כמו:
```
🔄 Generating content
📊 התקדמות: 20.0%
✅ הושלמו: 1 מתוך 5
⏱️ זמן שעבר: 15.3 שניות
--------------------------------------------------
🔄 Generating images
📊 התקדמות: 40.0%
✅ הושלמו: 2 מתוך 5
⏱️ זמן שעבר: 28.7 שניות
--------------------------------------------------
```

## מבנה הקלאסים העיקריים ב-workflow.py

### WorkflowStep
מייצג שלב בודד בתהליך:
```python
@dataclass
class WorkflowStep:
    name: str                           # שם השלב
    description: str                    # תיאור השלב
    required: bool = True               # האם השלב חובה
    dependencies: List[str]             # שלבים שתלויים בו
    estimated_duration: float = 0.0    # זמן משוער בשניות
```

### StepResult
תוצאת ביצוע שלב:
```python
@dataclass
class StepResult:
    step_name: str                      # שם השלב
    success: bool                       # האם הצליח
    start_time: datetime                # זמן התחלה
    end_time: Optional[datetime]        # זמן סיום
    result_data: Optional[Any]          # נתוני התוצאה
    error: Optional[Exception]          # שגיאה אם הייתה
    cleanup_actions: List[Callable]     # פעולות ניקיון
```

### WorkflowProgress
מעקב התקדמות כללית:
```python
@dataclass
class WorkflowProgress:
    current_step: str                   # השלב הנוכחי
    completed_steps: List[str]          # שלבים שהושלמו
    failed_steps: List[str]             # שלבים שנכשלו
    total_steps: int                    # סך השלבים
    start_time: Optional[datetime]      # זמן התחלה
    estimated_completion: Optional[datetime]  # זמן סיום משוער
```

### ResourceManager
ניהול קבצים זמניים ומשאבים:
```python
class ResourceManager:
    def __init__(self, base_dir=None, cleanup_on_exit=True)
    def create_temp_dir(self, prefix="presentation_gen_") -> Path
    def create_temp_file(self, suffix="", prefix="temp_") -> Path
    def register_cleanup_action(self, action: Callable) -> None
    def cleanup_all(self) -> None
```

### WorkflowManager
המנהל הראשי של כל התהליך:
```python
class WorkflowManager:
    def __init__(self, config: Config)
    def set_progress_callback(self, callback: Callable) -> None
    def execute_workflow(self, topic, content_generator, image_processor, 
                        audio_processor=None, video_assembler=None) -> PresentationResult
    def get_current_progress(self) -> Optional[WorkflowProgress]
    def get_step_results(self) -> Dict[str, StepResult]
    def cancel_workflow(self) -> None
```

## זרימת העבודה המלאה

1. **אתחול**: יצירת WorkflowManager עם קונפיגורציה
2. **הגדרת callback**: קביעת פונקציית עדכון התקדמות
3. **ביצוע שלבים**:
   - יצירת תוכן עם AI
   - המרה לתמונות
   - יצירת קריינות (אופציונלי)
   - הרכבת וידאו (אופציונלי)
   - סיום וניקיון
4. **מעקב**: עדכון progress_callback בכל שלב
5. **ניקיון**: מחיקת קבצים זמניים

## יתרונות המבנה הזה

- **שקיפות**: אתה רואה בדיוק מה קורה ומתי
- **בקרה**: אפשר לעצור או לשנות התנהגות בכל שלב
- **אמינות**: טיפול מקיף בשגיאות וניקיון משאבים
- **ביצועים**: עיבוד מקבילי כשאפשר
- **תחזוקה**: קוד מאורגן וקל להבנה
- **הרחבה**: קל להוסיף שלבים חדשים או לשנות קיימים

בקיצור, ה-`workflow.py` הוא הלב של המערכת - הוא מתאם הכל, עוקב אחרי ההתקדמות, ומאפשר לך לדעת מה קורה בכל רגע נתון.