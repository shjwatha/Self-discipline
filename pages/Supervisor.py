import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.graph_objects as go

# ===== التحقق من تسجيل الدخول =====
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔐 يجب تسجيل الدخول أولاً")
    st.switch_page("home.py")

permissions = st.session_state.get("permissions")
if permissions not in ["supervisor", "sp"]:
    if permissions == "admin":
        st.switch_page("pages/AdminDashboard.py")
    elif permissions == "user":
        st.switch_page("pages/UserDashboard.py")
    else:
        st.switch_page("home.py")

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

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


admin_sheet = spreadsheet.worksheet("admin")
users_df = pd.DataFrame(admin_sheet.get_all_records())
chat_sheet = spreadsheet.worksheet("chat")

username = st.session_state.get("username")

# ===== إعداد الصفحة =====
st.set_page_config(page_title="📊 تقارير المشرف", page_icon="📊", layout="wide")

# ===== ضبط اتجاه النص إلى اليمين =====
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

st.title(f"👋 أهلاً {st.session_state.get('full_name')}")

# ===== تحديد المستخدمين المتاحين للمحادثة =====
all_user_options = []

if permissions == "sp":
    my_supervisors = users_df[(users_df["role"] == "supervisor") & (users_df["Mentor"] == username)]["username"].tolist()
    all_user_options += [(s, "مشرف") for s in my_supervisors]

if permissions in ["supervisor", "sp"]:
    assigned_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"].isin([username] + [s for s, _ in all_user_options]))]
    all_user_options += [(u, "مستخدم") for u in assigned_users["username"].tolist()]

# إضافة سوبر مشرفين (إن وُجدوا) إلى القائمة للدردشة معهم
# ===== تحميل بيانات الطلاب لعرض التقارير =====
if permissions == "supervisor":
    filtered_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"] == username)]
elif permissions == "sp":
    supervised_supervisors = users_df[(users_df["role"] == "supervisor") & (users_df["Mentor"] == username)]["username"].tolist()
    filtered_users = users_df[(users_df["role"] == "user") & (users_df["Mentor"].isin(supervised_supervisors))]
else:
    filtered_users = pd.DataFrame()

all_data = []
users_with_data = []
all_usernames = filtered_users["username"].tolist()

for _, user in filtered_users.iterrows():
    user_name = user["username"]
    sheet_name = user["sheet_name"]
    try:
        user_ws = spreadsheet.worksheet(sheet_name)
        user_records = user_ws.get_all_records()
        df = pd.DataFrame(user_records)
        if "التاريخ" in df.columns:
            df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
            df.insert(0, "username", user_name)
            all_data.append(df)
            users_with_data.append(user_name)
    except Exception as e:
        st.warning(f"⚠️ خطأ في تحميل بيانات {user_name}: {e}")

if not all_data:
    st.info("ℹ️ لا توجد بيانات.")
    st.stop()

merged_df = pd.concat(all_data, ignore_index=True)

# ====== تبويبات الصفحة ======
tabs = st.tabs([" تقرير إجمالي", "💬 المحادثات", "📋 تجميعي الكل", "📌 تجميعي بند", " تقرير فردي", "📈 رسوم بيانية"])


# ===== دالة عرض المحادثة =====

def show_chat_supervisor():
    st.subheader("💬 الدردشة")

    if "selected_user_display" not in st.session_state:
        st.session_state["selected_user_display"] = "اختر الشخص"


# تأكد من استخدام "full_name" بدلاً من "username" في جميع المحادثات
    options_display = ["اختر الشخص"] + [f"{full_name} ({role})" for full_name, role in all_user_options]


    selected_display = st.selectbox("اختر الشخص", options_display, key="selected_user_display")

    if selected_display != "اختر الشخص":
        selected_user = selected_display.split(" (")[0]

        chat_data = pd.DataFrame(chat_sheet.get_all_records())

        # تحقق من أن البيانات ليست فارغة
        if chat_data.empty:
            st.info("💬 لا توجد رسائل بعد.")
        else:
            # تحقق من وجود الأعمدة المطلوبة
            required_columns = {"timestamp", "from", "to", "message", "read_by_receiver"}
            if not required_columns.issubset(chat_data.columns):
                st.warning(f"⚠️ الأعمدة المطلوبة غير موجودة في ورقة الدردشة. الأعمدة الموجودة: {chat_data.columns}")
                return

            # حذف أي بيانات فارغة في الحقول المطلوبة
            chat_data = chat_data.dropna(subset=["timestamp", "from", "to", "message", "read_by_receiver"])

            # تحديث حالة القراءة
            unread_indexes = chat_data[
                (chat_data["from"] == selected_user) &
                (chat_data["to"] == username) &
                (chat_data["read_by_receiver"].astype(str).str.strip() == "")
            ].index.tolist()

            for i in unread_indexes:
                chat_sheet.update_cell(i + 2, 5, "✓")  # الصف +2 لأن الصف الأول للعناوين

            # عرض الرسائل
            messages = chat_data[((chat_data["from"] == username) & (chat_data["to"] == selected_user)) |
                                 ((chat_data["from"] == selected_user) & (chat_data["to"] == username))]
            messages = messages.sort_values(by="timestamp")

            if messages.empty:
                st.info("💬 لا توجد رسائل بعد.")
            else:
                for _, msg in messages.iterrows():
                    if msg["from"] == username:
                        st.markdown(f"<p style='color:#8B0000'><b>‍ أنت:</b> {msg['message']}</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='color:#000080'><b> {msg['from']}:</b> {msg['message']}</p>", unsafe_allow_html=True)

        # حقل النص لإدخال الرسالة
        new_msg = st.text_area("✏️ اكتب رسالتك", height=100, key="chat_message")
        if st.button("📨 إرسال الرسالة"):
            if new_msg.strip():  # تأكد من أن الرسالة ليست فارغة
                timestamp = (datetime.utcnow() + pd.Timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
                chat_sheet.append_row([timestamp, username, selected_user, new_msg, ""])
        
                # رسالة تم إرسالها
                st.success("✅ تم إرسال الرسالة")

                # إعادة تحميل الصفحة بعد الإرسال
                st.rerun()

                # مسح النص في حقل النص
                del st.session_state["chat_message"]
            else:
                st.warning("⚠️ لا يمكن إرسال رسالة فارغة.")







# ===== تبويب 1: تقرير إجمالي =====
with tabs[0]:
    # === تنبيه بالرسائل غير المقروءة ===
    chat_data = pd.DataFrame(chat_sheet.get_all_records())
    
    # تحقق من وجود الأعمدة المطلوبة
    required_columns = ["to", "message", "read_by_receiver", "from"]
    if all(col in chat_data.columns for col in required_columns):
        unread_msgs = chat_data[
            (chat_data["to"] == username) &
            (chat_data["message"].notna()) &
            (chat_data["read_by_receiver"].astype(str).str.strip() == "")
        ]
        senders = unread_msgs["from"].unique().tolist()
        if senders:
            sender_list = "، ".join(senders)
            st.markdown(f"<p style='color:red; font-weight:bold;'>يوجد لديك عدد دردشات لم تطلع عليها من ({sender_list})</p>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ لا يوجد لديك دردشات تأكد يجب الضغط على أيقونة جلب المعلومات من قاعدة البيانات دائما'.")

    st.subheader(" مجموع درجات كل مستخدم")
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_2"):
        st.cache_data.clear()
        st.rerun()
    scores = merged_df.drop(columns=["التاريخ", "username"], errors="ignore")
    grouped = merged_df.groupby("username")[scores.columns].sum()
    grouped["المجموع"] = grouped.sum(axis=1, numeric_only=True)
    grouped = grouped.sort_values(by="المجموع", ascending=True)
    for user, row in grouped.iterrows():
        full_name = users_df.loc[users_df["username"] == user, "full_name"].values[0]
        st.markdown(f"### <span style='color: #006400;'>{full_name} : {row['المجموع']} درجة</span>", unsafe_allow_html=True)


# ===== تبويب 2: المحادثات =====
with tabs[1]:
    show_chat_supervisor()







# ===== تبويب 3: تجميعي الكل =====
with tabs[2]:
    st.subheader("📋 تفاصيل الدرجات للجميع")
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_3"):
        st.cache_data.clear()
        st.rerun()
    st.dataframe(grouped, use_container_width=True)

# ===== تبويب 4: تجميعي بند =====
with tabs[3]:
    st.subheader("📌 مجموع بند لمستخدم")
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_4"):
        st.cache_data.clear()
        st.rerun()
    all_columns = [col for col in merged_df.columns if col not in ["التاريخ", "username"]]
    selected_activity = st.selectbox("اختر البند", all_columns)
    activity_sum = merged_df.groupby("username")[selected_activity].sum().sort_values(ascending=True)
    missing_users = set(all_usernames) - set(users_with_data)
    for user in missing_users:
        activity_sum[user] = 0
    st.dataframe(activity_sum, use_container_width=True)

# ===== تبويب 5: تقرير فردي =====
with tabs[4]:
    st.subheader("تقرير تفصيلي لمستخدم")
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_5"):
        st.cache_data.clear()
        st.rerun()

    # إضافة عمود "full_name" إلى merged_df
    merged_df["full_name"] = merged_df["username"].map(lambda x: users_df.loc[users_df["username"] == x, "full_name"].values[0])

    # استخدام "full_name" في selectbox
    selected_user = st.selectbox("اختر المستخدم", merged_df["full_name"].unique())

    # الآن يمكننا استخدام "full_name" لعرض البيانات
    user_df = merged_df[merged_df["full_name"] == selected_user].sort_values("التاريخ")
    st.dataframe(user_df.reset_index(drop=True), use_container_width=True)

# ===== تبويب 6: رسوم بيانية =====
with tabs[5]:
    st.subheader("📈 رسوم بيانية")
    if st.button("🔄 جلب المعلومات من قاعدة البيانات", key="refresh_6"):
        st.cache_data.clear()
        st.rerun()
    scores = merged_df.drop(columns=["التاريخ", "username"], errors="ignore")
    grouped = merged_df.groupby("username")[scores.columns].sum()
    grouped["المجموع"] = grouped.sum(axis=1, numeric_only=True)
    fig = go.Figure(go.Pie(
        labels=grouped.index,
        values=grouped["المجموع"],
        hole=0.4,
        title="مجموع الدرجات"
    ))
    st.plotly_chart(fig, use_container_width=True)
