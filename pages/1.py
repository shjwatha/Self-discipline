from supabase import create_client, Client
import datetime

# بيانات الاتصال بـ Supabase
SUPABASE_URL = "https://ybdmuwjjlfrwtesoqhqz.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# بيانات المدير العام
full_name = "المدير العام"
username = "jwatha"
password = "Admin@123"
role = "super_admin"

# التحقق من عدم التكرار
check = supabase.table("super_admins").select("*").eq("username", username).execute()
if check.data:
    print("❌ اسم المستخدم مستخدم من قبل. لا يمكن إنشاء الحساب.")
else:
    result = supabase.table("super_admins").insert({
        "full_name": full_name,
        "username": username,
        "password": password,
        "role": role,
        "created_at": datetime.datetime.now().isoformat()
    }).execute()
    print("✅ تم إنشاء حساب المدير العام بنجاح.")

