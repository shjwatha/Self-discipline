from supabase import create_client, Client
import datetime

# بيانات الاتصال بـ Supabase
SUPABASE_URL = "https://ybdmuwjjlfrwtesoqhqz.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliZG11d2pqbGZyd3Rlc29xaHF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc2MjE5MzIsImV4cCI6MjA2MzE5NzkzMn0.1Fpa-RZlTeOt8EeBHZwEn0OoWY-WGyH40GE1W1GOAck"

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

