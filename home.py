import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعداد الصفحة =====
st.set_page_config(page_title="تسجيل الدخول", page_icon="🔐")
st.title("🔐 تسجيل الدخول")

# زر التحديث اليدوي
if st.button("🔄 جلب المعلومات من قاعدة البيانات"):
    st.cache_data.clear()
    st.success("✅ تم تحديث البيانات")

# مدخلات وهمية لإخفاء اقتراحات iOS
st.markdown("""
<input type="text" name="fake_username" style="opacity:0; position:absolute; top:-1000px;">
<input type="password" name="fake_password" style="opacity:0; position:absolute; top:-1000px;">
""", unsafe_allow_html=True)

# حالة المصادقة الافتراضية
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# معرفات ملفات Google Sheets (15 مستوى)
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

# نموذج تسجيل الدخول
if not st.session_state["authenticated"]:
    with st.form("login_form"):
        input_value = st.text_input("اسم المستخدم أو الاسم الكامل")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("دخول")

        if submitted:
            # تصفير بيانات الجلسة قبل البدء
            for key in ["username", "full_name", "permissions", "sheet_name", "sheet_id", "level"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state["authenticated"] = False

            status_msg = st.info("⏳ جاري توجيهك لملف البيانات الخاص بك قد يستغرق الأمر دقيقة أو دقيقتين...")
            user_found = False

            for level_name, sheet_id in SHEET_IDS.items():
                try:
                    sheet = client.open_by_key(sheet_id).worksheet("admin")
                    df = pd.DataFrame(sheet.get_all_records())

                    match = df[
                        ((df["username"] == input_value) | (df["full_name"] == input_value)) &
                        (df["password"] == password)
                    ]


                    st.write(f"🔍 محاولة في {level_name} ({sheet_id})")
                    st.write(match)

                    if not match.empty:
                        row = match.iloc[0]
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = row["username"]
                        st.session_state["full_name"] = row["full_name"]
                        st.session_state["permissions"] = row["role"]
                        st.session_state["sheet_name"] = row["sheet_name"]
                        st.session_state["sheet_id"] = sheet_id
                        st.session_state["level"] = level_name
                        user_found = True
                        break

                except:
                    continue  # تجاهل الأخطاء

            status_msg.empty()
            if not user_found:
                # تصفير الجلسة بالكامل بعد فشل الدخول
                st.session_state["authenticated"] = False
                for key in ["username", "full_name", "permissions", "sheet_name", "sheet_id", "level"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
            else:
                st.success("✅ تم تسجيل الدخول بنجاح")
                role = st.session_state["permissions"]
                if role == "admin":
                    st.switch_page("pages/AdminDashboard.py")
                elif role in ["supervisor", "sp"]:
                    st.switch_page("pages/Supervisor.py")
                elif role == "user":
                    st.switch_page("pages/UserDashboard.py")
                else:
                    st.error("⚠️ صلاحية غير معروفة.")
else:
    # التوجيه التلقائي إذا سبق الدخول
    role = st.session_state.get("permissions")
    if role == "admin":
        st.switch_page("pages/AdminDashboard.py")
    elif role in ["supervisor", "sp"]:
        st.switch_page("pages/Supervisor.py")
    elif role == "user":
        st.switch_page("pages/UserDashboard.py")
    else:
        st.error("⚠️ صلاحية غير معروفة.")
