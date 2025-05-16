import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from hijri_converter import Hijri, Gregorian


# ===== إعادة التوجيه إلى صفحة تسجيل الدخول إذا لم يتم تسجيل الدخول =====
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("home.py")

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعداد الصفحة =====
st.set_page_config(page_title="تقييم اليوم", page_icon="📋", layout="wide")

# ===== تحقق من صلاحية المستخدم =====
if "username" not in st.session_state or "sheet_url" not in st.session_state:
    st.error("❌ يجب تسجيل الدخول أولاً.")
    st.stop()

if st.session_state["permissions"] != "user":
    if st.session_state["permissions"] == "admin":
        st.warning(" تم تسجيل الدخول كأدمن، سيتم تحويلك للوحة التحكم...")
        st.switch_page("pages/AdminDashboard.py")
    elif st.session_state["permissions"] in ["supervisor", "sp"]:
        st.warning(" تم تسجيل الدخول كمشرف، سيتم تحويلك للتقارير...")
        st.switch_page("pages/Supervisor.py")
    else:
        st.error("⚠️ صلاحية غير معروفة.")
    st.stop()

username = st.session_state["username"]
sheet_name = f"بيانات - {username}"
try:
    spreadsheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY")
except Exception:
    st.error("❌ حدث خطأ أثناء الاتصال بقاعدة البيانات. حاول مرة أخرى.")
    st.markdown("""<script>
        setTimeout(function() {
            window.location.href = "/home";
        }, 1000);
    </script>""", unsafe_allow_html=True)
    st.stop()

worksheet = spreadsheet.worksheet(sheet_name)
columns = worksheet.row_values(1)

# ===== جلب اسم المشرف =====
admin_sheet = spreadsheet.worksheet("admin")
admin_data = pd.DataFrame(admin_sheet.get_all_records())
mentor_name = admin_data.loc[admin_data["username"] == username, "Mentor"].values[0]

# جلب السوبر مشرف إن وجد
sp_row = admin_data[(admin_data["username"] == mentor_name)]
sp_name = sp_row["Mentor"].values[0] if not sp_row.empty else None

if not columns:
    st.error("❌ لم يتم العثور على الأعمدة في ورقة البيانات.")
    st.stop()

def refresh_button(key):
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key=key):
        st.cache_data.clear()
        st.rerun()

def load_data():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# ===== دالة عرض المحادثة =====

def show_chat():
    st.markdown("### 💬 المحادثة مع المشرفين")

    options = [mentor_name]
    if sp_name:
        options.append(sp_name)

    # استخدام خيار افتراضي
    if "selected_mentor_display" not in st.session_state:
        st.session_state["selected_mentor_display"] = "اختر الشخص"

    options_display = ["اختر الشخص"] + options
    selected_mentor_display = st.selectbox("📨 اختر الشخص الذي ترغب بمراسلته", options_display, key="selected_mentor_display")

    if selected_mentor_display != "اختر الشخص":
        selected_mentor = selected_mentor_display

        chat_sheet = spreadsheet.worksheet("chat")
        raw_data = chat_sheet.get_all_records()
        chat_data = pd.DataFrame(raw_data) if raw_data else pd.DataFrame(columns=["timestamp", "from", "to", "message", "read_by_receiver"])

        if not {"from", "to", "message", "timestamp"}.issubset(chat_data.columns):
            st.warning("⚠️ لم يتم العثور على الأعمدة الصحيحة في ورقة الدردشة.")
            return

        # تحديث حالة القراءة
        if "read_by_receiver" in chat_data.columns:
            unread_indexes = chat_data[
                (chat_data["from"] == selected_mentor) &
                (chat_data["to"] == username) &
                (chat_data["read_by_receiver"].astype(str).str.strip() == "")
            ].index.tolist()

            for i in unread_indexes:
                chat_sheet.update_cell(i + 2, 5, "✓")  # الصف +2 لأن الصف الأول للعناوين

        # استخراج الرسائل بعد التحديث
        messages = chat_data[((chat_data["from"] == username) & (chat_data["to"] == selected_mentor)) |
                             ((chat_data["from"] == selected_mentor) & (chat_data["to"] == username))]
        messages = messages.sort_values(by="timestamp")

        if messages.empty:
            st.info("💬 لا توجد رسائل حالياً.")
        else:
            for _, msg in messages.iterrows():
                if msg["from"] == username:
                    st.markdown(f"<p style='color:#000080'><b> أنت:</b> {msg['message']}</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color:#8B0000'><b> {msg['from']}:</b> {msg['message']}</p>", unsafe_allow_html=True)

        new_msg = st.text_area("✏️ اكتب رسالتك هنا", height=100)
        if st.button("📨 إرسال الرسالة"):
            if new_msg.strip():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                chat_sheet.append_row([timestamp, username, selected_mentor, new_msg, ""])
                st.success("✅ تم إرسال الرسالة")
                st.rerun()
            else:
                st.warning("⚠️ لا يمكن إرسال رسالة فارغة.")




# ===== التبويبات =====
tabs = st.tabs(["📝 إدخال البيانات", "💬 المحادثات", "📊 تقارير المجموع"])

# ===== التبويب الأول: إدخال البيانات =====


with tabs[0]:

    st.markdown(
        """
        <style>
        body, .stTextInput, .stTextArea, .stSelectbox, .stButton, .stMarkdown, .stDataFrame {
            direction: rtl;
            text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # تصغير "أهلاً ... مجموعتك"
    st.markdown(f"<h3 style='color: #0000FF; font-weight: bold; font-size: 24px;'>👋 أهلاً {username} | مجموعتك / {mentor_name}</h3>", unsafe_allow_html=True)

    # تصغير "المحاسبة الذاتية"
    st.markdown("<h4 style='color: #0000FF; font-weight: bold; font-size: 20px;'>📝 المحاسبة الذاتية</h4>", unsafe_allow_html=True)

    refresh_button("refresh_tab1")



# ===== تنبيه بالرسائل غير المقروءة =====
    chat_sheet = spreadsheet.worksheet("chat")
    chat_data = pd.DataFrame(chat_sheet.get_all_records())

    if "read_by_receiver" in chat_data.columns:
        unread_msgs = chat_data[
            (chat_data["to"] == username) &
            (chat_data["message"].notna()) &
            (chat_data["read_by_receiver"].astype(str).str.strip() == "")
        ]
        senders = unread_msgs["from"].unique().tolist()
        if senders:
            sender_list = "، ".join(senders)
            st.markdown(f"""
    <table style="width:100%;">
    <tr>
    <td style="direction: rtl; text-align: right; color: red; font-weight: bold; font-size: 16px;">
    📬 يوجد لديك رسائل لم تطلع عليها من: ({sender_list})
    </td>
    </tr>
    </table>
    """, unsafe_allow_html=True)

    with st.form("daily_form"):
        today = datetime.today().date()

        # توليد آخر 7 تواريخ بالهجري
        hijri_dates = []
        for i in range(7):
            g_date = today - timedelta(days=i)
            h_date = Gregorian(g_date.year, g_date.month, g_date.day).to_hijri()
            weekday = g_date.strftime("%A")
            arabic_weekday = {
                "Saturday": "السبت",
                "Sunday": "الأحد",
                "Monday": "الاثنين",
                "Tuesday": "الثلاثاء",
                "Wednesday": "الأربعاء",
                "Thursday": "الخميس",
                "Friday": "الجمعة"
            }[weekday]
            hijri_label = f"{arabic_weekday} - {h_date.day}/{h_date.month}/{h_date.year} هـ"
            hijri_dates.append((hijri_label, g_date))

        # إنشاء قائمة اختيار من التواريخ الهجرية
        hijri_labels = [label for label, _ in hijri_dates]
        selected_label = st.selectbox("📅 اختر التاريخ (هجري)", hijri_labels)
        selected_date = dict(hijri_dates)[selected_label]  # هذا هو التاريخ الميلادي المطابق

        values = [selected_date.strftime("%Y-%m-%d")]



# الاختيارات الأولى: الأعمدة الخمسة الأولى بدون تعديل
        st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>الاختيارات الأولى</h3>", unsafe_allow_html=True)
        options_1 = ["في المسجد جماعة", "في المنزل جماعة", "في المسجد منفرد", "في المنزل منفرد", "خارج الوقت"]
        ratings_1 = {
            "في المسجد جماعة": 5,
            "في المنزل جماعة": 4,
            "في المسجد منفرد": 3,
            "في المنزل منفرد": 2,
            "خارج الوقت": 0
        }
        
        for col in columns[1:6]:
            st.markdown(f"<h4 style='font-weight: bold;'>{col}</h4>", unsafe_allow_html=True)
            rating = st.radio(col, options_1, index=0, key=col)
            values.append(str(ratings_1[rating]))
        
        # العمود السادس: خيارات متعددة (Checkboxes) – كل خيار 1 درجة
        st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>العمود السادس: أوقات الصلاة (كل اختيار 1 درجة)</h3>", unsafe_allow_html=True)
        checkbox_options = ["الفجر", "الظهر", "العصر", "المغرب", "العشاء"]
        st.markdown(f"<h4 style='font-weight: bold;'>{columns[6]}</h4>", unsafe_allow_html=True)
        
        # نضع الخيارات في سطر منفصل باستخدام st.columns(1)
        checkbox_cols = st.columns(1)
        selected_checkboxes = []
        for option in checkbox_options:
            with checkbox_cols[0]:
                if st.checkbox(option, key=f"{columns[6]}_{option}"):
                    selected_checkboxes.append(option)
        score_checkbox = len(selected_checkboxes)  # كل خيار مختار يعطي درجة واحدة
        values.append(str(score_checkbox))
        
        # العمود السابع والثامن: تقييم القراءة بخيارات اختيار واحد
        st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>العمود السابع والثامن: تقييم القراءة</h3>", unsafe_allow_html=True)
        time_read_options = ["قرأته لفترتين", "قرأته مرة واحدة في اليوم", "لم أتمكن من قراءته لهذا اليوم"]
        ratings_read = {"قرأته لفترتين": 2, "قرأته مرة واحدة في اليوم": 1, "لم أتمكن من قراءته لهذا اليوم": 0}
        for col_name in columns[7:9]:
            st.markdown(f"<h4 style='font-weight: bold;'>{col_name}</h4>", unsafe_allow_html=True)
            rating = st.radio("", time_read_options, horizontal=True, key=col_name)
            values.append(str(ratings_read[rating]))
        
        # الأعمدة من 9 إلى 14: إجابتان نعم أو لا (إذا كانت الإجابة نعم تعطي 2 درجة، ولا تعطي 0)
        st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>العمود 9 إلى 14: تقييم بنعم أو لا (نعم = 2 درجة، لا = 0)</h3>", unsafe_allow_html=True)
        yes_no_options = ["نعم", "لا"]
        ratings_yes2 = {"نعم": 2, "لا": 0}
        for col_name in columns[9:15]:
            st.markdown(f"<h4 style='font-weight: bold;'>{col_name}</h4>", unsafe_allow_html=True)
            rating = st.radio("", yes_no_options, horizontal=True, key=col_name)
            values.append(str(ratings_yes2[rating]))
        
        # باقي الأعمدة إذا وُجدت: إجابتان نعم أو لا (نعم = 1 درجة، لا = 0)
        if len(columns) > 15:
            st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>بقية الأعمدة: تقييم بنعم أو لا (نعم = 1 درجة، لا = 0)</h3>", unsafe_allow_html=True)
            remaining_columns = columns[15:]
            for col_name in remaining_columns:
                st.markdown(f"<h4 style='font-weight: bold;'>{col_name}</h4>", unsafe_allow_html=True)
                rating = st.radio("", yes_no_options, horizontal=True, key=col_name)
                values.append(str(ratings_yes1[rating]))
        
        # زر الإرسال والحفظ
        submit = st.form_submit_button("💾 حفظ")
        
        if submit:
            if selected_date not in [d for _, d in hijri_dates]:
                st.error("❌ التاريخ غير صالح. لا يمكن حفظ البيانات لأكثر من أسبوع سابق فقط")
            else:
                all_dates = worksheet.col_values(1)
                date_str = selected_date.strftime("%Y-%m-%d")
                try:
                    row_index = all_dates.index(date_str) + 1
                except ValueError:
                    row_index = len(all_dates) + 1
                    worksheet.update_cell(row_index, 1, date_str)
                for i, val in enumerate(values[1:], start=2):
                    worksheet.update_cell(row_index, i, val)
        
                st.cache_data.clear()
                data = load_data()
                st.success("✅ تم الحفظ بنجاح والاتصال بقاعدة البيانات") 
        








# ===== التبويب الثاني: المحادثة =====
with tabs[1]:

    st.markdown(
    """
    <style>
    body, .stTextInput, .stTextArea, .stSelectbox, .stButton, .stMarkdown, .stDataFrame {
        direction: rtl;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True
)

    
    refresh_button("refresh_chat")
    show_chat()



# ===== التبويب الثالث: تقارير المجموع =====
with tabs[2]:
    st.title("📊 مجموع البنود للفترة")
    refresh_button("refresh_tab2")

    st.markdown("<h3 style='color: #0000FF; font-weight: bold;'>التقارير</h3>", unsafe_allow_html=True)

    df = pd.DataFrame(worksheet.get_all_records())
    df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    if "البند" in df.columns and "المجموع" in df.columns:
        df = df.dropna(subset=["البند", "المجموع"])

    if "رقم التسلسل" in df.columns:
        df = df.drop(columns=["رقم التسلسل"])

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("من تاريخ", datetime.today().date() - timedelta(days=7))
    with col2:
        end_date = st.date_input("إلى تاريخ", datetime.today().date())

    mask = (df["التاريخ"] >= pd.to_datetime(start_date)) & (df["التاريخ"] <= pd.to_datetime(end_date))
    filtered = df[mask].drop(columns=["التاريخ"], errors="ignore")

    if filtered.empty:
        st.warning("⚠️ لا توجد بيانات في الفترة المحددة.")
    else:
        totals = filtered.sum(numeric_only=True)
        total_score = totals.sum()

        st.metric(label="📌 مجموعك الكلي لجميع البنود", value=int(total_score))

        result_df = pd.DataFrame(totals, columns=["المجموع"])
        result_df.index.name = "البند"
        result_df = result_df.reset_index()
        result_df = result_df.sort_values(by="المجموع", ascending=True)

        result_df = result_df[["المجموع", "البند"]]
        result_df["البند"] = result_df["البند"].apply(lambda x: f"<p style='color:#8B0000; text-align:center'>{x}</p>")
        result_df["المجموع"] = result_df["المجموع"].apply(lambda x: f"<p style='color:#000080; text-align:center'>{x}</p>")

        st.markdown(result_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    
