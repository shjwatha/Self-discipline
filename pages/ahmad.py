import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials

# إعداد الاتصال بقاعدة بيانات Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# التحقق من الجلسة وصلاحيات المستخدم
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔐 يجب تسجيل الدخول أولاً")
    st.switch_page("home.py")

if st.session_state.get("permissions") != "admin":
    role = st.session_state.get("permissions")
    if role == "user":
        st.switch_page("pages/UserDashboard.py")
    else:
        st.switch_page("home.py")

# فتح ورقة المستخدمين (لوحة الأدمن)
try:
    spreadsheet = client.open_by_key(st.session_state["sheet_id"])
    admin_sheet = spreadsheet.worksheet("admin")
    users_df = pd.DataFrame(admin_sheet.get_all_records())
except Exception as e:
    if "Quota exceeded" in str(e) or "429" in str(e):
        st.error("❌ لقد تجاوزت عدد المرات المسموح بها الاتصال بقاعدة البيانات في الدقيقة. يرجى المحاولة مجددًا بعد دقيقة.")
    else:
        st.error("❌ حدث خطأ أثناء تحميل ملف المستخدمين الخاص بك. يرجى المحاولة لاحقًا.")
    st.stop()

# قائمة المشرفين للمدخلات
supervisors_df = users_df[users_df["role"] == "supervisor"]
mentor_options = supervisors_df["username"].tolist()

# ضبط اتجاه النص إلى RTL لجميع حقول الإدخال
st.markdown("""
<style>
input, select {
  unicode-bidi: bidi-override;
  direction: RTL;
}
</style>
""", unsafe_allow_html=True)

# إعداد الصفحة وعنوانها
st.set_page_config(page_title="لوحة إدارة المستخدمين", page_icon="🛠️")
st.title("🛠️ لوحة إدارة المستخدمين")

st.subheader("➕ إنشاء حسابات مستخدمين جديدة (حتى 20 حسابًا دفعة واحدة)")
with st.form("create_multiple_users_form"):
    for i in range(1, 21):
        cols = st.columns(4)
        cols[0].text_input(f"الاسم الكامل للمستخدم {i}", key=f"full_name_{i}")
        cols[1].text_input(f"اسم المستخدم {i}", key=f"username_{i}")
        cols[2].text_input(f"كلمة المرور {i}", type="password", key=f"password_{i}")
        cols[3].selectbox(f"اختر المشرف {i}", mentor_options, key=f"mentor_{i}")

    save_button = st.form_submit_button("💾 حفظ جميع المستخدمين")

if save_button:
    skip_count = 0
    # جلب بيانات جميع الملفات الخارجية للتحقق من التكرار
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
    existing_usernames = set()
    existing_fullnames = set()
    for sid in SHEET_IDS.values():
        try:
            sheet = client.open_by_key(sid).worksheet("admin")
            df = pd.DataFrame(sheet.get_all_records())
            for _, row in df.iterrows():
                existing_usernames.add(str(row["username"]).strip().lower())
                existing_fullnames.add(str(row["full_name"]).strip().lower())
        except:
            continue

    # معالجة كل صف من صفوف الإدخال
    for i in range(1, 21):
        full_name = st.session_state.get(f"full_name_{i}", "").strip()
        username = st.session_state.get(f"username_{i}", "").strip()
        password = st.session_state.get(f"password_{i}", "").strip()
        mentor = st.session_state.get(f"mentor_{i}", "")

        # تجاهل الصف الفارغ تمامًا
        if full_name == "" and username == "" and password == "":
            continue
        # التحقق من ملء جميع الحقول
        if not full_name or not username or not password:
            st.warning(f"⚠️ يرجى تعبئة جميع الحقول في السطر {i} بالكامل.")
            continue

        # التحقق من عدم التكرار
        full_clean = full_name.lower()
        user_clean = username.lower()
        if full_clean in existing_usernames or full_clean in existing_fullnames \
           or user_clean in existing_usernames or user_clean in existing_fullnames:
            st.warning(f"⚠️ تم تخطي المستخدم \"{full_name}\"؛ الاسم الكامل أو اسم المستخدم موجود مسبقًا.")
            skip_count += 1
            continue

        # إضافة ورقة المستخدم الجديد والأعمدة الافتراضية
        try:
            worksheet_name = f"بيانات - {username}"
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=30)
            default_cols = [
                "التاريخ", "صلاة الفجر", "صلاة الظهر", "صلاة العصر", "صلاة المغرب", "صلاة العشاء",
                "السنن الرواتب", "ورد الإمام النووي رحمه الله", "مختصر إشراق الضياء",
                "سنة الوتر", "سنة الضحى", "درس - قراءة (شرعي)", "تلاوة قرآن (لا يقل عن ثمن)",
                "الدعاء مخ العبادة", "لا إله إلا الله", "الاستغفار",
                "الصلاة على سيدنا رسول الله صلى الله عليه وسلم"
            ]
            worksheet.insert_row(default_cols, 1)
            admin_sheet.append_row([full_name, username, password, worksheet_name, "user", mentor])
            st.success(f"✅ تم إنشاء حساب المستخدم \"{full_name}\" بنجاح")
        except Exception as e:
            if "already exists" in str(e):
                st.warning(f"⚠️ اسم المستخدم \"{full_name}\" موجود مسبقًا، لم يتم الإنشاء.")
            else:
                st.error(f"❌ حدث خطأ أثناء إنشاء المستخدم \"{full_name}\": {e}")

    # عرض عدد المستخدمين الذين تم تخطيهم بسبب التكرار
    if skip_count > 0:
        st.info(f"⚠️ تم تخطي {skip_count} مستخدمًا بسبب التكرار في البيانات.")
