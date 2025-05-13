import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.graph_objects as go

# ===== الاتصال بـ Google Sheets =====
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

# ===== إعداد الصفحة =====
st.set_page_config(page_title="التقارير", page_icon="📊")
st.title("📊 التقارير")

# ===== تحقق من صلاحية المشرف =====
if "permissions" not in st.session_state or st.session_state["permissions"] != "supervisor":
    st.error("🚫 هذه الصفحة مخصصة للمشرف فقط.")
    st.stop()

# ===== التبويبات: اختيار نوع التقرير =====
tab = st.selectbox("اختار نوع التقرير", ["تقرير تجميعي", "تقرير بند معين", "تقرير فردي", "الرسوم البيانية"])

# جلب بيانات المستخدمين
admin_sheet = client.open_by_key("1gOmeFwHnRZGotaUHqVvlbMtVVt1A2L7XeIuolIyJjAY").worksheet("admin")
users_df = pd.DataFrame(admin_sheet.get_all_records())
user_sheets = users_df["sheet_name"].values  # هنا نتعامل مع العامود الثالث الذي يحتوي على روابط الشيتات

# تاريخ بداية ونهاية الفترات
start_date = st.date_input("تاريخ البداية", datetime(2025, 1, 1))
end_date = st.date_input("تاريخ النهاية", datetime.today())

# تقرير تجميعي - جمع الدرجات لجميع البنود لفترة معينة
if tab == "تقرير تجميعي":
    aggregated_data = []
    
    for sheet_url in user_sheets:
        try:
            user_spreadsheet = client.open_by_url(sheet_url)  # فتح الشيت باستخدام الرابط الفعلي
            user_worksheet = user_spreadsheet.get_worksheet(0)  # تحديد الورقة الأولى
            user_data = user_worksheet.get_all_records()  # جلب البيانات من الورقة الأولى
            if not user_data:
                st.warning(f"📄 الورقة {sheet_url} فارغة.")
            else:
                # تحويل البيانات إلى DataFrame إذا كانت موجودة
                user_data_df = pd.DataFrame(user_data)
                user_data_df['التاريخ'] = pd.to_datetime(user_data_df['التاريخ'], errors='coerce')  # تأكد من تحويل التاريخ
                # تصفية البيانات بناءً على التاريخ
                user_data_df = user_data_df[(user_data_df['التاريخ'] >= pd.to_datetime(start_date)) & 
                                             (user_data_df['التاريخ'] <= pd.to_datetime(end_date))]
                # جمع الدرجات لجميع البنود
                user_data_df['المجموع'] = user_data_df.iloc[:, 1:].sum(axis=1)  # جمع الدرجات لجميع الأعمدة
                aggregated_data.append({
                    'الاسم': user_spreadsheet.title,
                    'المجموع': user_data_df['المجموع'].sum()  # جمع درجات جميع الأيام
                })
                
        except Exception as e:
            st.error(f"⚠️ حدث خطأ في جلب البيانات من الشيت {sheet_url}: {str(e)}")
    
    aggregated_df = pd.DataFrame(aggregated_data)
    st.dataframe(aggregated_df)

# تقرير بند معين - جمع درجات بند معين
elif tab == "تقرير بند معين":
    # اختيار البند
    selected_column = st.selectbox("اختار البند", users_df.columns[1:])
    aggregated_column_data = []
    
    for sheet_url in user_sheets:
        try:
            user_spreadsheet = client.open_by_url(sheet_url)  # فتح الشيت باستخدام الرابط الفعلي
            user_worksheet = user_spreadsheet.get_worksheet(0)  # تحديد الورقة الأولى
            user_data = user_worksheet.get_all_records()  # جلب البيانات من الورقة الأولى
            if not user_data:
                st.warning(f"📄 الورقة {sheet_url} فارغة.")
            else:
                # تحويل البيانات إلى DataFrame
                user_data_df = pd.DataFrame(user_data)
                user_data_df['التاريخ'] = pd.to_datetime(user_data_df['التاريخ'], errors='coerce')  # تأكد من تحويل التاريخ
                # تصفية البيانات بناءً على التاريخ
                user_data_df = user_data_df[(user_data_df['التاريخ'] >= pd.to_datetime(start_date)) & 
                                             (user_data_df['التاريخ'] <= pd.to_datetime(end_date))]
                # جمع الدرجات للبند المحدد
                aggregated_column_data.append({
                    'الاسم': user_spreadsheet.title,
                    selected_column: user_data_df[selected_column].sum()  # جمع درجات البند
                })
                
        except Exception as e:
            st.error(f"⚠️ حدث خطأ في جلب البيانات من الشيت {sheet_url}: {str(e)}")
    
    column_data_df = pd.DataFrame(aggregated_column_data)
    st.dataframe(column_data_df)

# تقرير فردي - جمع درجات شخص معين لفترة معينة
elif tab == "تقرير فردي":
    # اختيار اسم المستخدم
    selected_user = st.selectbox("اختار الشخص", users_df["username"].values)
    user_sheet_url = users_df[users_df["username"] == selected_user]["sheet_name"].values[0]
    
    try:
        user_spreadsheet = client.open_by_url(user_sheet_url)  # فتح الشيت باستخدام الرابط الفعلي
        user_worksheet = user_spreadsheet.get_worksheet(0)  # تحديد الورقة الأولى
        user_data = user_worksheet.get_all_records()  # جلب البيانات من الورقة الأولى
        if not user_data:
            st.warning(f"📄 الورقة {selected_user} فارغة.")
        else:
            # تحويل البيانات إلى DataFrame
            user_data_df = pd.DataFrame(user_data)
            user_data_df['التاريخ'] = pd.to_datetime(user_data_df['التاريخ'], errors='coerce')  # تأكد من تحويل التاريخ
            # تصفية البيانات بناءً على التاريخ
            user_data_df = user_data_df[(user_data_df['التاريخ'] >= pd.to_datetime(start_date)) & 
                                         (user_data_df['التاريخ'] <= pd.to_datetime(end_date))]
            # جمع الدرجات لجميع البنود
            user_data_df['المجموع'] = user_data_df.iloc[:, 1:].sum(axis=1)
            
            st.subheader(f"تقرير فردي للمستخدم: {selected_user}")
            st.dataframe(user_data_df)
        
    except Exception as e:
        st.error(f"⚠️ حدث خطأ في جلب البيانات للمستخدم {selected_user}: {str(e)}")

# تبويب الرسوم البيانية (Pie charts)
elif tab == "الرسوم البيانية":
    st.subheader("📊 الرسوم البيانية")
    
    # تقرير تجميعي (Pie Chart)
    aggregated_data = []
    for sheet_url in user_sheets:
        try:
            user_spreadsheet = client.open_by_url(sheet_url)  # فتح الشيت باستخدام الرابط الفعلي
            user_worksheet = user_spreadsheet.get_worksheet(0)  # تحديد الورقة الأولى
            user_data = user_worksheet.get_all_records()
            if not user_data:
                st.warning(f"📄 الورقة {sheet_url} فارغة.")
            else:
                user_data_df = pd.DataFrame(user_data)
                user_data_df['التاريخ'] = pd.to_datetime(user_data_df['التاريخ'], errors='coerce')
                user_data_df = user_data_df[(user_data_df['التاريخ'] >= pd.to_datetime(start_date)) & 
                                             (user_data_df['التاريخ'] <= pd.to_datetime(end_date))]
                user_data_df['المجموع'] = user_data_df.iloc[:, 1:].sum(axis=1)
                aggregated_data.append(user_data_df['المجموع'].sum())
                
        except Exception as e:
            st.error(f"⚠️ حدث خطأ في جلب البيانات من الشيت {sheet_url}: {str(e)}")
    
    # إنشاء دائرة واحدة (Pie Chart)
    fig = go.Figure(data=[go.Pie(labels=[f"المستخدم {i+1}" for i in range(len(aggregated_data))], values=aggregated_data)])
    st.plotly_chart(fig)
