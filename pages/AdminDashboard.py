import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials

# ===== إعداد الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== التحقق من الجلسة =====
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔐 يجب تسجيل الدخول أولاً")
    st.switch_page("home.py")

if st.session_state.get("permissions") != "admin":
    role = st.session_state.get("permissions")
    if role == "user":
        st.switch_page("pages/UserDashboard.py")
    elif role in ["supervisor", "sp"]:
        st.switch_page("pages/Supervisor.py")
    else:
        st.switch_page("home.py")

# ===== تحميل الملف الخاص بالأدمن =====
try:
    spreadsheet = client.open_by_key(st.session_state["sheet_id"])
    admin_sheet = spreadsheet.worksheet("admin")
    users_df = pd.DataFrame(admin_sheet.get_all_records())
except Exception as e:
    st.error(f"❌ تعذر تحميل الملف الخاص بك: {e}")
    st.stop()

# ===== إعداد الصفحة =====
st.set_page_config(page_title="لوحة الأدمن", page_icon="🛠️")
st.title("🛠️ لوحة إدارة المستخدمين")

if st.button("🔄 جلب المعلومات من قاعدة البيانات"):
    st.cache_data.clear()
    st.rerun()

# ===== الأعمدة الافتراضية لكل مستخدم جديد =====
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

# ===== قراءة المشرفين =====
supervisors_df = users_df[users_df["role"] == "supervisor"]

# ===== إنشاء مستخدم جديد =====
st.subheader("➕ إنشاء حساب جديد")
with st.form("create_user_form"):
    full_name = st.text_input("الاسم الكامل")
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور")
    role = "user"

    mentor_options = supervisors_df["username"].tolist()
    mentor = st.selectbox("اختر المشرف", mentor_options)

    create = st.form_submit_button("إنشاء")

    if create:
        if not username or not password or not full_name or not mentor:
            st.warning("يرجى تعبئة جميع الحقول المطلوبة")
        else:
            # ===== التحقق من التكرار في جميع الملفات =====
            SHEET_IDS = {
                "المستوى 1":  "1Jx6MsOy4x5u7XsWFx1G3HpdQS1Ic5_HOEogbnWCXA3c",
                "المستوى 2":  "1kyNn69CTM661nNMhiestw3VVrH6rWrDQl7-dN5eW0kQ",
                "المستوى 3":  "1rZT2Hnc0f4pc4qKctIRt_eH6Zt2O8yF-SIpS66IzhNU",
                "المستوى 4":  "19L878i-iQtZgHgqFThSFgWJBFpTsQFiD5QS7lno8rsI",
                "المستوى 5":  "1YimetyT4xpKGheuN-TFm5J8w6k6cf3yIwQXRmvIqTW0",
                "المستوى 6":  "1Fxo3XgJHCJgcuXseNjmRePRH4L0t6gpkDv0Sz0Tm_u8",
                "المستوى 7":  "1t5u5qE8tXSChK4ezshF5FZ_eYMpjR_00xsp4CUrPp5c",
                "المستوى 8":  "1crt5ERYxrt8Cg1YkcK40CkO3Bribr3vOMmOkttDpR1A",
                "المستوى 9":  "1v4asV17nPg2u62eYsy1dciQX5WnVqNRmXrWfTY2jvD0",
                "المستوى 10": "15waTwimthOdMTeqGS903d8ELR8CtCP3ZivIYSsgLmP4",
                "المستوى 11": "1BSqbsfjw0a4TM-C0W0pIh7IhqzZ8jU3ZhFy8gu4CMWo",
                "المستوى 12": "1AtsVnicX_6Ew7Oci3xP77r6W3yA-AhntlT3TNGcbPbM",
                "المستوى 13": "1jcCGm1rfW_6bNg8tyaK6aOyKvXuC4Jc2w-wrjiDX20s",
                "المستوى 14": "1qkhZjgftc7Ro9pGJGdydICHQb0yUtV8P9yWzSCD3ewo",
                "المستوى 15": "1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY"
            }

            is_duplicate = False
            for sid in SHEET_IDS.values():
                try:
                    sheet = client.open_by_key(sid).worksheet("admin")
                    df = pd.DataFrame(sheet.get_all_records())
                    if username in df["username"].astype(str).values or username in df["full_name"].astype(str).values \
                       or full_name in df["full_name"].astype(str).values or full_name in df["username"].astype(str).values:
                        is_duplicate = True
                        break
                except:
                    continue

            if is_duplicate:
                st.error("🚫 اسم المستخدم محجوز من قبل شخص آخر")
            else:
                try:


                    worksheet_name = f"بيانات - {username}"
                    worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="1000", cols="30")
                    worksheet.insert_row(get_default_columns(), 1)
                    admin_sheet.append_row([full_name, username, password, worksheet_name, role, mentor])
                    st.success("✅ تم إنشاء المستخدم والورقة بنجاح")
                    st.rerun()
                except Exception as e:
                    if "already exists" in str(e):
                        st.error("❌ الاسم الكامل مستخدم من قبل شخص آخر")
                    else:
                        st.error(f"❌ حدث خطأ أثناء إنشاء المستخدم: {e}")
