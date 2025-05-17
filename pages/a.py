import streamlit as st
import gspread
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="إعداد الملفات", page_icon="🛠️")

st.title("🛠️ إنشاء الأوراق الأساسية في ملفات Google Sheets")

# تحميل بيانات الاعتماد
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# روابط الملفات بدون الرابط الأساسي
SHEET_IDS = [
    "1Jx6MsOy4x5u7XsWFx1G3HpdQS1Ic5_HOEogbnWCXA3c",
    "1kyNn69CTM661nNMhiestw3VVrH6rWrDQl7-dN5eW0kQ",
    "1rZT2Hnc0f4pc4qKctIRt_eH6Zt2O8yF-SIpS66IzhNU",
    "19L878i-iQtZgHgqFThSFgWJBFpTsQFiD5QS7lno8rsI",
    "1YimetyT4xpKGheuN-TFm5J8w6k6cf3yIwQXRmvIqTW0",
    "1Fxo3XgJHCJgcuXseNjmRePRH4L0t6gpkDv0Sz0Tm_u8",
    "1t5u5qE8tXSChK4ezshF5FZ_eYMpjR_00xsp4CUrPp5c",
    "1crt5ERYxrt8Cg1YkcK40CkO3Bribr3vOMmOkttDpR1A",
    "1v4asV17nPg2u62eYsy1dciQX5WnVqNRmXrWfTY2jvD0",
    "15waTwimthOdMTeqGS903d8ELR8CtCP3ZivIYSsgLmP4",
    "1BSqbsfjw0a4TM-C0W0pIh7IhqzZ8jU3ZhFy8gu4CMWo",
    "1AtsVnicX_6Ew7Oci3xP77r6W3yA-AhntlT3TNGcbPbM",
    "1jcCGm1rfW_6bNg8tyaK6aOyKvXuC4Jc2w-wrjiDX20s",
    "1qkhZjgftc7Ro9pGJGdydICHQb0yUtV8P9yWzSCD3ewo"
]

# محتويات الأوراق
admin_headers = ["full_name", "username", "password", "sheet_name", "role", "Mentor"]
chat_headers = ["timestamp", "from", "to", "message", "read_by_receiver"]
notes_headers = ["timestamp", "الطالب", "المشرف", "الملاحظة"]

if st.button("🚀 تنفيذ وإنشاء الأوراق"):
    for sheet_id in SHEET_IDS:
        try:
            sheet = client.open_by_key(sheet_id)
            existing_sheets = [ws.title for ws in sheet.worksheets()]

            def create_if_not_exists(name, headers):
                if name not in existing_sheets:
                    ws = sheet.add_worksheet(title=name, rows="1000", cols="10")
                    ws.insert_row(headers, 1)
                    st.success(f"✅ تم إنشاء الورقة '{name}' في الملف: {sheet.title}")
                else:
                    st.info(f"ℹ️ الورقة '{name}' موجودة بالفعل في: {sheet.title}")

            create_if_not_exists("admin", admin_headers)
            create_if_not_exists("chat", chat_headers)
            create_if_not_exists("notes", notes_headers)

        except Exception as e:
            st.error(f"❌ خطأ في الملف {sheet_id}: {e}")
