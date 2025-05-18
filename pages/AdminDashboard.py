import streamlit as st
import gspread
import pandas as pd
import json
import re
import time
from google.oauth2.service_account import Credentials

# دالة استخراج مفتاح الملف من الرابط باستخدام تعبير نمطي
def extract_spreadsheet_id(url):
    pattern = r"/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# قائمة روابط ملفات جوجل شيت (15 ملف)
sheet_links = [
    "https://docs.google.com/spreadsheets/d/1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY",
    "https://docs.google.com/spreadsheets/d/1Jx6MsOy4x5u7XsWFx1G3HpdQS1Ic5_HOEogbnWCXA3c",
    "https://docs.google.com/spreadsheets/d/1kyNn69CTM661nNMhiestw3VVrH6rWrDQl7-dN5eW0kQ",
    "https://docs.google.com/spreadsheets/d/1rZT2Hnc0f4pc4qKctIRt_eH6Zt2O8yF-SIpS66IzhNU",
    "https://docs.google.com/spreadsheets/d/19L878i-iQtZgHgqFThSFgWJBFpTsQFiD5QS7lno8rsI",
    "https://docs.google.com/spreadsheets/d/1YimetyT4xpKGheuN-TFm5J8w6k6cf3yIwQXRmvIqTW0",
    "https://docs.google.com/spreadsheets/d/1Fxo3XgJHCJgcuXseNjmRePRH4L0t6gpkDv0Sz0Tm_u8",
    "https://docs.google.com/spreadsheets/d/1t5u5qE8tXSChK4ezshF5FZ_eYMpjR_00xsp4CUrPp5c",
    "https://docs.google.com/spreadsheets/d/1crt5ERYxrt8Cg1YkcK40CkO3Bribr3vOMmOkttDpR1A",
    "https://docs.google.com/spreadsheets/d/1v4asV17nPg2u62eYsy1dciQX5WnVqNRmXrWfTY2jvD0",
    "https://docs.google.com/spreadsheets/d/15waTwimthOdMTeqGS903d8ELR8CtCP3ZivIYSsgLmP4",
    "https://docs.google.com/spreadsheets/d/1BSqbsfjw0a4TM-C0W0pIh7IhqzZ8jU3ZhFy8gu4CMWo",
    "https://docs.google.com/spreadsheets/d/1AtsVnicX_6Ew7Oci3xP77r6W3yA-AhntlT3TNGcbPbM",
    "https://docs.google.com/spreadsheets/d/1jcCGm1rfW_6bNg8tyaK6aOyKvXuC4Jc2w-wrjiDX20s",
    "https://docs.google.com/spreadsheets/d/1qkhZjgftc7Ro9pGJGdydICHQb0yUtV8P9yWzSCD3ewo"
]

# دالة لجمع جميع سجلات المستخدمين من ملفات جوجل شيت الخمسة عشر
def get_all_users():
    all_users = []
    for link in sheet_links:
        sheet_id = extract_spreadsheet_id(link)
        try:
            spreadsheet_temp = client.open_by_key(sheet_id)
            admin_ws = spreadsheet_temp.worksheet("admin")
            df = pd.DataFrame(admin_ws.get_all_records())
            if not df.empty:
                all_users.append(df)
        except Exception:
            # تجاهل الملفات التي لا يمكن الوصول إليها أو التي تواجه مشاكل (مثل تجاوز الحصص)
            continue
    if all_users:
        return pd.concat(all_users, ignore_index=True)
    else:
        # إنشاء DataFrame فارغ مع الأعمدة المتوقعة لتفادي أخطاء المستقبل
        return pd.DataFrame(columns=["full_name", "username", "password", "worksheet_name", "role", "mentor"])

# ===== إعداد الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعادة توجيه حسب الصلاحيات =====
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔐 يجب تسجيل الدخول أولاً")
    st.switch_page("home.py")

if st.session_state.get("permissions") != "admin":
    permission = st.session_state.get("permissions")
    if permission == "user":
        st.switch_page("pages/UserDashboard.py")
    elif permission in ["supervisor", "sp"]:
        st.switch_page("pages/Supervisor.py")
    else:
        st.switch_page("home.py")

# ===== إعدادات الشيت الرئيسي =====
ADMIN_SHEET_ID = "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"
spreadsheet = client.open_by_key(ADMIN_SHEET_ID)
admin_sheet = spreadsheet.worksheet("admin")
users_df_local = pd.DataFrame(admin_sheet.get_all_records())

# ===== إعداد الصفحة =====
st.set_page_config(page_title="لوحة الأدمن", page_icon="🛠️")
st.title("🛠️ لوحة إدارة المستخدمين")

# زر التحديث اليدوي
if st.button("🔄 جلب المعلومات من قاعدة البيانات"):
    st.cache_data.clear()
    st.experimental_rerun()

# دالة لإرجاع الأعمدة الافتراضية لكل مستخدم جديد
def get_default_columns():
    return [
        "التاريخ",
        "صلاة الفجر",
        "صلاة الظهر",
        "صلاة العصر",
        "صلاة المغرب",
        "صلاة العشاء",
        "السنن الرواتب",
        "ورد الإمام النووي رحمه الله",
        "مختصر إشراق الضياء",
        "سنة الوتر",
        "سنة الضحى",
        "درس - قراءة ( شرعي )",
        "تلاوة قرآن (لا يقل عن ثمن)",
        "الدعاء مخ العبادة",
        "لا إله إلا الله",
        "الاستغفار",
        "الصلاة على سيدنا رسول الله صلى الله عليه وسلم"
    ]

# عرض المشرفين في النظام (يتم قراءة سجلات المشرفين من السجلات المحلية)
supervisors_df = users_df_local[users_df_local["role"] == "supervisor"]

# ===== إنشاء مستخدم جديد =====
st.subheader("➕ إنشاء حساب جديد")
with st.form("create_user_form"):
    # رفع الاسم الكامل أولاً ثم اسم المستخدم
    full_name = st.text_input("الاسم كاملاً")
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور")
    role = "user"  # تثبيت الصلاحية على user فقط

    # اختيار المشرف من قائمة المشرفين (يُعرض اسم المستخدم للمشرفين)
    mentor_options = supervisors_df["username"].tolist()
    mentor = st.selectbox("اختر المشرف", mentor_options)

    create = st.form_submit_button("إنشاء")

    if create:
        if not username or not password or not mentor or not full_name:
            st.warning("يرجى إدخال الاسم كاملاً واسم المستخدم وكلمة المرور واختيار المشرف")
        else:
            # تجميع بيانات المستخدمين من جميع ملفات جوجل شيت الخمسة عشر
            all_users_df = get_all_users()
            # التحقق من عدم تكرار اسم المستخدم أو الاسم الكامل في كل الملفات
            if (username in all_users_df["username"].values) or (username in all_users_df["full_name"].values):
                st.error("🚫 اسم المستخدم مستخدم مسبقًا كاسم مستخدم أو كاسم كامل")
            elif (full_name in all_users_df["full_name"].values) or (full_name in all_users_df["username"].values):
                st.error("🚫 الاسم الكامل مستخدم مسبقًا كاسم كامل أو كاسم مستخدم")
            else:
                try:
                    # إنشاء ورقة جديدة للمستخدم داخل الشيت الرئيسي (يمكن تعديل هذا الجزء لإنشاء ملف منفصل إذا رغبت)
                    worksheet_name = f"بيانات - {username}"
                    new_worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="1000", cols="30")
                    new_worksheet.insert_row(get_default_columns(), 1)
                    # إضافة سجل المستخدم إلى ورقة الأدمن في الشيت الرئيسي
                    admin_sheet.append_row([full_name, username, password, worksheet_name, role, mentor])
                    st.success("✅ تم إنشاء المستخدم والورقة بنجاح")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء إنشاء المستخدم: {e}")
