from supabase import create_client, Client

SUPABASE_URL = "https://ybdmuwjjlfrwtesoqhqz.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliZG11d2pqbGZyd3Rlc29xaHF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc2MjE5MzIsImV4cCI6MjA2MzE5NzkzMn0.1Fpa-RZlTeOt8EeBHZwEn0OoWY-WGyH40GE1W1GOAck"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

schema_sql = \"\"\"
-- جدول الأدمن
create table if not exists admins (
    id uuid primary key default gen_random_uuid(),
    full_name text,
    username text unique,
    password text,
    role text default 'admin',
    level integer,
    created_at timestamp default now()
);

-- جدول المستخدمين
create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    full_name text,
    username text unique,
    password text,
    level integer,
    mentor text,
    created_at timestamp default now()
);

-- جدول المحاسبة الذاتية اليومية
create table if not exists data (
    id bigserial primary key,
    user_id uuid references users(id),
    date date,
    col_1 integer,
    col_2 integer,
    col_3 integer,
    col_4 integer,
    col_5 integer,
    col_6 integer,
    col_7 integer,
    col_8 integer,
    col_9 integer,
    col_10 integer,
    col_11 integer,
    col_12 integer,
    col_13 integer,
    col_14 integer,
    col_15 integer,
    col_16 integer,
    created_at timestamp default now()
);

-- جدول المحادثة
create table if not exists chat (
    id bigserial primary key,
    from_user text,
    to_user text,
    message text,
    timestamp timestamp default now(),
    read_by_receiver boolean default false
);

-- جدول الملاحظات / الإنجازات
create table if not exists notes (
    id bigserial primary key,
    الطالب text,
    المشرف text,
    الملاحظة text,
    timestamp timestamp default now()
);

-- جدول قائمة الإنجازات (من ملف الكنترول)
create table if not exists achievements_list (
    id serial primary key,
    الإنجاز text
);

-- جدول السوبر آدمن
create table if not exists super_admins (
    id uuid primary key default gen_random_uuid(),
    full_name text,
    username text unique,
    password text,
    role text default 'super_admin',
    created_at timestamp default now()
);
\"\"\"

# تنفيذ السكربت
response = supabase.rpc("execute_sql", {"sql": schema_sql})
print("✅ تم تنفيذ سكربت إنشاء الجداول بنجاح" if not response.get("error") else f"❌ خطأ: {response['error']}")

