# texts.py
# מרכז את כל ההודעות שהבוט שולח למשתמש

TEXTS = {
    "welcome": (
        "👋 שלום וברוכים הבאים לבוט של GOK!\n\n"
        "📸 שלחו תמונה עם ברקוד ברור,\n"
        "👨‍💻 או הקלידו את המספר שעל הברקוד (13 ספרות).\n\n"
        "אענה לכם מיד עם מידע אודות כשרות המוצר."),
    "thanks" : (
        "🤖 אני בוט ואין צורך לומר לי תודה,\n"
        "🧙‍♂️ אם ברצונך להודות ליוצרי המיזם תוכל לתרום לארגון GOK בלינק:\n"
        "https://kosher.global/support-zekasher 🙏"),
    "errors": {
        "image_processing": "בעיה בעיבוד התמונה🔄",
        "unsupported_type": "סוג הודעה לא נתמך. נא לשלוח תמונה עם ברקוד או טקסט עם ספרות ברקוד.",
        "invalid_message": "הודעה לא קבילה. נא לשלוח תמונה עם ברקוד או טקסט עם ספרות ברקוד.",
        "exception": "שגיאה פנימית בטיפול בבקשה. אנא נסה שוב מאוחר יותר.",
        "barcode_not_found": "😲 לא נמצא ברקוד בתמונה",
        "unsupported_barcode": "בתמונה מופיע ברקוד שאיננו נתמך, נא לשלוח תמונה בה יש ברקוד סטנדרטי בלבד.",
        "internal_logic_error": "שגיאת שרת, נסה שוב מאוחר יותר⏳ או פנה לתמיכה🛠️",

        # GOK-related
        "gok_server_error": "שגיאת שרת בעת שאילתת GOK, נסה שוב מאוחר יותר⏳",
        "gok_not_found": "לא קיים מידע במערכת GOK😢",
    },
    "product_status": {
        "in_review": "⚠️ המוצר בבחינה",
        "not_kosher": "❌ לא כשר",
        "kosher_template": "{kashrut_type} ✅{cert}",
    },
    "barcode": {
        "prefix": "ברקוד: ",
    },
    "gok_strings": {
        "confirmed": 'מוצר מאושר ע"י הרב לשימוש במערכת',

    }
}

GOK_STATUS = {
    "confirmed": 'מוצר מאושר ע"י הרב לשימוש במערכת',
    "not_kosher": "לא כשר",
}

HELP_KEYWORDS = ["hi", "hello", "hey", "שלום", "היי", "הי", "start", "help", "עזרה"]
THANKS_KEYWORDS = ["thank", "tnx", "תודה", "אשריך"]