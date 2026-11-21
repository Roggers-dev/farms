from datetime import date, datetime
import os
import sqlite3
import uuid
import pandas as pd
import streamlit as st

try:
  import sqlalchemy

  SQLALCHEMY_AVAILABLE = True
except ImportError:
  SQLALCHEMY_AVAILABLE = False

st.set_page_config(
    page_title="Animal Farm Management System",
    page_icon="🐄",
    layout="wide",
)

SQLITE_PATH = "animal_farm_management.db"

ANIMAL_CATEGORIES = [
    "Pigs / Swine",
    "Poultry (Broilers / Layers)",
    "Cattle",
    "Goats",
    "Sheep",
    "Rabbits",
    "Other Livestock",
]

ANIMAL_IMAGES = {
    "Pigs / Swine": (
        "https://images.unsplash.com/photo-1516467508483-a7212febe31a?auto=format&fit=crop&w=800&h=520&fit=crop&q=80"
    ),
    "Poultry (Broilers / Layers)": (
        "https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?auto=format&fit=crop&w=800&h=520&fit=crop&q=80"
    ),
    "Cattle": (
        "https://images.unsplash.com/photo-1570042225831-d98fa7577f1e?auto=format&fit=crop&w=800&h=520&fit=crop&q=80"
    ),
    "Goats": (
        "https://images.unsplash.com/photo-1524024973431-2ad916746881?auto=format&fit=crop&w=800&h=520&fit=crop&q=80"
    ),
    "Sheep": (
        "https://images.unsplash.com/photo-1484557985045-edf25e08da73?auto=format&fit=crop&w=800&h=520&fit=crop&q=80"
    ),
    "Rabbits": (
        "https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?auto=format&fit=crop&w=800&h=520&fit=crop&q=80"
    ),
    "Other Livestock": (
        "https://images.unsplash.com/photo-1500595046711-ee27150ad24e?auto=format&fit=crop&w=800&h=520&fit=crop&q=80"
    ),
}

QUANTITY_PRESETS = [
    1,
    2,
    5,
    10,
    20,
    25,
    50,
    100,
    200,
    500,
    1000,
    "Custom (Type below)",
]

st.markdown(
    """
    <style>
    .uniform-animal-card img {
        width: 100% !important;
        height: 210px !important;
        object-fit: cover !important;
        border-radius: 10px !important;
    }
    .uniform-hero-img img {
        width: 100% !important;
        height: 260px !important;
        object-fit: cover !important;
        border-radius: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_uniform_image(url, caption="", hero=False):
  css_cls = "uniform-hero-img" if hero else "uniform-animal-card"
  st.markdown(f'<div class="{css_cls}">', unsafe_allow_html=True)
  st.image(url, caption=caption, use_container_width=True)
  st.markdown("</div>", unsafe_allow_html=True)


def quantity_selector(label, key_prefix, default_preset=10, min_val=0.0, step=1.0):
  col_dd, col_txt = st.columns([1, 1])
  default_idx = (
      QUANTITY_PRESETS.index(default_preset)
      if default_preset in QUANTITY_PRESETS
      else 0
  )
  choice = col_dd.selectbox(
      f"{label} (Quick Select)",
      QUANTITY_PRESETS,
      index=default_idx,
      key=f"{key_prefix}_dd",
  )
  initial_val = (
      float(choice) if isinstance(choice, (int, float)) else float(default_preset)
  )
  typed_val = col_txt.number_input(
      f"Type Exact {label}",
      min_value=float(min_val),
      value=float(initial_val),
      step=float(step),
      key=f"{key_prefix}_num",
  )
  return float(typed_val)


def get_configured_db_url():
  try:
    for section in ("postgres", "neon"):
      sec = st.secrets.get(section, {})
      if isinstance(sec, dict) and sec.get("url"):
        return str(sec["url"]).strip()
    top_url = st.secrets.get("url", "") or st.secrets.get("DATABASE_URL", "")
    if top_url:
      return str(top_url).strip()
  except Exception:
    pass

  env_url = os.environ.get("DATABASE_URL", "").strip()
  if env_url:
    return env_url

  return ""


@st.cache_resource
def get_pg_engine():
  if not SQLALCHEMY_AVAILABLE:
    return None, "SQLAlchemy not installed (using SQLite)."
  raw_url = get_configured_db_url()
  if not raw_url:
    return None, "No PostgreSQL URL configured (using SQLite)."

  pg_url = raw_url
  if pg_url.startswith("postgresql://") and "+psycopg2" not in pg_url:
    pg_url = pg_url.replace("postgresql://", "postgresql+psycopg2://", 1)

  try:
    engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
    with engine.connect() as conn:
      db_name = conn.execute(
          sqlalchemy.text("SELECT current_database()")
      ).scalar()
    return engine, f"Connected to PostgreSQL ({db_name})"
  except Exception as exc:
    return None, f"PostgreSQL unavailable, using SQLite ({exc})"


def use_postgres(engine):
  return engine is not None and SQLALCHEMY_AVAILABLE


def init_db(engine):
  if use_postgres(engine):
    with engine.begin() as conn:
      conn.execute(
          sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    password TEXT NOT NULL
                )
            """)
      )
      conn.execute(
          sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS animals (
                    id_number TEXT PRIMARY KEY,
                    animal_type TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    date_brought TEXT NOT NULL,
                    sex TEXT NOT NULL,
                    cost DOUBLE PRECISION DEFAULT 0.0,
                    date_of_birth TEXT,
                    crossing_date TEXT,
                    farrow_date TEXT,
                    status TEXT DEFAULT 'Active',
                    plan_buy_date TEXT,
                    plan_sell_date TEXT
                )
            """)
      )
      conn.execute(
          sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS feed_and_mortality (
                    id SERIAL PRIMARY KEY,
                    animal_type TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    id_number TEXT,
                    feed_type TEXT NOT NULL,
                    food_type TEXT NOT NULL,
                    food_quantity_of_what TEXT,
                    quantity DOUBLE PRECISION DEFAULT 0.0,
                    unit_cost DOUBLE PRECISION DEFAULT 0.0,
                    total_cost DOUBLE PRECISION DEFAULT 0.0,
                    date_recorded TEXT NOT NULL,
                    date_finish TEXT,
                    mortality_count INTEGER DEFAULT 0,
                    mortality_of_what TEXT,
                    death_count INTEGER DEFAULT 0,
                    death_of_what TEXT,
                    date_of_mortality TEXT,
                    date_of_death TEXT,
                    other_expenses DOUBLE PRECISION DEFAULT 0.0
                )
            """)
      )
      for col_ddl in [
          "ALTER TABLE feed_and_mortality ADD COLUMN IF NOT EXISTS food_quantity_of_what TEXT",
          "ALTER TABLE feed_and_mortality ADD COLUMN IF NOT EXISTS mortality_of_what TEXT",
          "ALTER TABLE feed_and_mortality ADD COLUMN IF NOT EXISTS death_count INTEGER DEFAULT 0",
          "ALTER TABLE feed_and_mortality ADD COLUMN IF NOT EXISTS death_of_what TEXT",
          "ALTER TABLE feed_and_mortality ADD COLUMN IF NOT EXISTS date_of_death TEXT",
      ]:
        conn.execute(sqlalchemy.text(col_ddl))

      conn.execute(
          sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS health_logs (
                    id SERIAL PRIMARY KEY,
                    id_number TEXT NOT NULL,
                    animal_type TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    visit_date TEXT NOT NULL,
                    disease TEXT NOT NULL,
                    medication TEXT NOT NULL,
                    vet_cost DOUBLE PRECISION DEFAULT 0.0
                )
            """)
      )
      conn.execute(
          sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS inventory_and_sales (
                    id SERIAL PRIMARY KEY,
                    record_type TEXT NOT NULL,
                    animal_type TEXT NOT NULL,
                    id_number TEXT,
                    item_or_batch TEXT NOT NULL,
                    quantity DOUBLE PRECISION DEFAULT 1.0,
                    unit_price DOUBLE PRECISION DEFAULT 0.0,
                    total_amount DOUBLE PRECISION DEFAULT 0.0,
                    record_date TEXT NOT NULL,
                    plan_buy_time TEXT,
                    plan_sell_time TEXT
                )
            """)
      )
      conn.execute(
          sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS animal_products (
                    id SERIAL PRIMARY KEY,
                    animal_id TEXT NOT NULL,
                    animal_type TEXT NOT NULL,
                    room_number TEXT,
                    product_category TEXT NOT NULL,
                    product_detail TEXT,
                    quantity DOUBLE PRECISION DEFAULT 0.0,
                    unit_label TEXT,
                    record_date TEXT NOT NULL,
                    notes TEXT
                )
            """)
      )
      conn.execute(
          sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    role TEXT,
                    pay_cycle TEXT NOT NULL,
                    pay_rate DOUBLE PRECISION DEFAULT 0.0,
                    credit_owed DOUBLE PRECISION DEFAULT 0.0,
                    loan_balance DOUBLE PRECISION DEFAULT 0.0
                )
            """)
      )
      conn.execute(
          sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS worker_finance_logs (
                    id SERIAL PRIMARY KEY,
                    worker_id TEXT NOT NULL,
                    worker_name TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    amount DOUBLE PRECISION NOT NULL,
                    entry_date TEXT NOT NULL,
                    notes TEXT
                )
            """)
      )
      conn.execute(
          sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS farm_loans (
                    loan_id TEXT PRIMARY KEY,
                    lender_name TEXT NOT NULL,
                    principal_amount DOUBLE PRECISION NOT NULL,
                    amount_paid DOUBLE PRECISION DEFAULT 0.0,
                    balance_due DOUBLE PRECISION NOT NULL,
                    date_taken TEXT NOT NULL,
                    notes TEXT
                )
            """)
      )
      conn.execute(
          sqlalchemy.text("""
                INSERT INTO users (username, full_name, role, password)
                VALUES ('admin', 'Farm Administrator', 'admin', 'admin123')
                ON CONFLICT (username) DO NOTHING
            """)
      )
      conn.execute(
          sqlalchemy.text("""
                INSERT INTO users (username, full_name, role, password)
                VALUES ('staff', 'Farm Supervisor', 'staff', 'staff123')
                ON CONFLICT (username) DO NOTHING
            """)
      )
  else:
    with sqlite3.connect(SQLITE_PATH) as conn:
      conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    password TEXT NOT NULL
                )
            """)
      conn.execute("""
                CREATE TABLE IF NOT EXISTS animals (
                    id_number TEXT PRIMARY KEY,
                    animal_type TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    date_brought TEXT NOT NULL,
                    sex TEXT NOT NULL,
                    cost REAL DEFAULT 0.0,
                    date_of_birth TEXT,
                    crossing_date TEXT,
                    farrow_date TEXT,
                    status TEXT DEFAULT 'Active',
                    plan_buy_date TEXT,
                    plan_sell_date TEXT
                )
            """)
      conn.execute("""
                CREATE TABLE IF NOT EXISTS feed_and_mortality (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    animal_type TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    id_number TEXT,
                    feed_type TEXT NOT NULL,
                    food_type TEXT NOT NULL,
                    food_quantity_of_what TEXT,
                    quantity REAL DEFAULT 0.0,
                    unit_cost REAL DEFAULT 0.0,
                    total_cost REAL DEFAULT 0.0,
                    date_recorded TEXT NOT NULL,
                    date_finish TEXT,
                    mortality_count INTEGER DEFAULT 0,
                    mortality_of_what TEXT,
                    death_count INTEGER DEFAULT 0,
                    death_of_what TEXT,
                    date_of_mortality TEXT,
                    date_of_death TEXT,
                    other_expenses REAL DEFAULT 0.0
                )
            """)
      existing_cols = {
          row[1]
          for row in conn.execute("PRAGMA table_info(feed_and_mortality)").fetchall()
      }
      migrations = {
          "food_quantity_of_what": "ALTER TABLE feed_and_mortality ADD COLUMN food_quantity_of_what TEXT",
          "mortality_of_what": "ALTER TABLE feed_and_mortality ADD COLUMN mortality_of_what TEXT",
          "death_count": "ALTER TABLE feed_and_mortality ADD COLUMN death_count INTEGER DEFAULT 0",
          "death_of_what": "ALTER TABLE feed_and_mortality ADD COLUMN death_of_what TEXT",
          "date_of_death": "ALTER TABLE feed_and_mortality ADD COLUMN date_of_death TEXT",
      }
      for col_name, ddl in migrations.items():
        if col_name not in existing_cols:
          conn.execute(ddl)

      conn.execute("""
                CREATE TABLE IF NOT EXISTS health_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_number TEXT NOT NULL,
                    animal_type TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    visit_date TEXT NOT NULL,
                    disease TEXT NOT NULL,
                    medication TEXT NOT NULL,
                    vet_cost REAL DEFAULT 0.0
                )
            """)
      conn.execute("""
                CREATE TABLE IF NOT EXISTS inventory_and_sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_type TEXT NOT NULL,
                    animal_type TEXT NOT NULL,
                    id_number TEXT,
                    item_or_batch TEXT NOT NULL,
                    quantity REAL DEFAULT 1.0,
                    unit_price REAL DEFAULT 0.0,
                    total_amount REAL DEFAULT 0.0,
                    record_date TEXT NOT NULL,
                    plan_buy_time TEXT,
                    plan_sell_time TEXT
                )
            """)
      conn.execute("""
                CREATE TABLE IF NOT EXISTS animal_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    animal_id TEXT NOT NULL,
                    animal_type TEXT NOT NULL,
                    room_number TEXT,
                    product_category TEXT NOT NULL,
                    product_detail TEXT,
                    quantity REAL DEFAULT 0.0,
                    unit_label TEXT,
                    record_date TEXT NOT NULL,
                    notes TEXT
                )
            """)
      conn.execute("""
                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    role TEXT,
                    pay_cycle TEXT NOT NULL,
                    pay_rate REAL DEFAULT 0.0,
                    credit_owed REAL DEFAULT 0.0,
                    loan_balance REAL DEFAULT 0.0
                )
            """)
      conn.execute("""
                CREATE TABLE IF NOT EXISTS worker_finance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_id TEXT NOT NULL,
                    worker_name TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    entry_date TEXT NOT NULL,
                    notes TEXT
                )
            """)
      conn.execute("""
                CREATE TABLE IF NOT EXISTS farm_loans (
                    loan_id TEXT PRIMARY KEY,
                    lender_name TEXT NOT NULL,
                    principal_amount REAL NOT NULL,
                    amount_paid REAL DEFAULT 0.0,
                    balance_due REAL NOT NULL,
                    date_taken TEXT NOT NULL,
                    notes TEXT
                )
            """)
      conn.execute("""
                INSERT OR IGNORE INTO users (username, full_name, role, password)
                VALUES ('admin', 'Farm Administrator', 'admin', 'admin123')
            """)
      conn.execute("""
                INSERT OR IGNORE INTO users (username, full_name, role, password)
                VALUES ('staff', 'Farm Supervisor', 'staff', 'staff123')
            """)


def _convert_sql_and_params(query, params, pg_mode):
  if not pg_mode:
    return query, params
  parts = query.split("?")
  if len(parts) == 1:
    return query, params
  bind_params = {}
  rebuilt = [parts[0]]
  for idx, val in enumerate(params):
    key = f"p{idx}"
    bind_params[key] = val
    rebuilt.append(f":{key}{parts[idx + 1]}")
  return "".join(rebuilt), bind_params


def read_df(engine, query, params=()):
  pg_mode = use_postgres(engine)
  sql_str, bind_vals = _convert_sql_and_params(query, params, pg_mode)
  if pg_mode:
    with engine.connect() as conn:
      return pd.read_sql(sqlalchemy.text(sql_str), conn, params=bind_vals)
  with sqlite3.connect(SQLITE_PATH) as conn:
    return pd.read_sql(sql_str, conn, params=params)


def exec_sql(engine, query, params=()):
  pg_mode = use_postgres(engine)
  sql_str, bind_vals = _convert_sql_and_params(query, params, pg_mode)
  if pg_mode:
    with engine.begin() as conn:
      conn.execute(sqlalchemy.text(sql_str), bind_vals)
  else:
    with sqlite3.connect(SQLITE_PATH) as conn:
      conn.execute(sql_str, params)
      conn.commit()


def authenticate_user(engine, username, password):
  df = read_df(
      engine,
      "SELECT id, username, full_name, role, password FROM users WHERE LOWER(username) = LOWER(?)",
      (username.strip(),),
  )
  if df.empty:
    return None
  row = df.iloc[0]
  if row["password"] == password:
    return {
        "id": int(row["id"]),
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
    }
  return None


def calc_days_spent_and_left(start_str, finish_str):
  today = date.today()
  days_spent = 0
  days_left = 0
  if start_str:
    try:
      d_start = datetime.strptime(str(start_str)[:10], "%Y-%m-%d").date()
      days_spent = max(0, (today - d_start).days)
    except ValueError:
      days_spent = 0
  if finish_str:
    try:
      d_fin = datetime.strptime(str(finish_str)[:10], "%Y-%m-%d").date()
      days_left = (d_fin - today).days
    except ValueError:
      days_left = 0
  return days_spent, days_left


pg_engine, db_status_msg = get_pg_engine()
init_db(pg_engine)

if "farm_user" not in st.session_state:
  st.session_state.farm_user = None
if "selected_animal_type" not in st.session_state:
  st.session_state.selected_animal_type = ANIMAL_CATEGORIES[0]
if "nav_section" not in st.session_state:
  st.session_state.nav_section = "🐾 Animals & Categories"


def select_animal_and_jump_to_entry(animal_cat):
  st.session_state.selected_animal_type = animal_cat
  st.session_state.nav_section = "🐾 Animals & Categories"


def render_sign_in():
  st.title("🐄 Animal Farm Management System — Sign In")
  st.caption(
      "Sign in with your Admin or Staff credentials to manage livestock, feed, "
      "health, inventory, products, sales, workers, and loans."
  )
  if use_postgres(pg_engine):
    st.success(f"🟢 {db_status_msg}")
  else:
    st.warning(f"🟡 {db_status_msg}")

  tab_admin, tab_staff = st.tabs(["🛡️ Admin Sign In", "👤 Staff Sign In"])

  with tab_admin:
    st.subheader("Administrator Sign In")
    st.info("Default Admin credentials: username `admin` | password `admin123`")
    with st.form("admin_sign_in_form"):
      adm_user = st.text_input("Admin Username", value="admin").strip()
      adm_pass = st.text_input("Admin Password", type="password").strip()
      if st.form_submit_button("Sign In as Admin", type="primary"):
        auth = authenticate_user(pg_engine, adm_user, adm_pass)
        if auth and auth["role"] == "admin":
          st.session_state.farm_user = auth
          st.success(f"Welcome, {auth['full_name']}!")
          st.rerun()
        elif auth:
          st.error("This account does not have Administrator privileges.")
        else:
          st.error("Invalid admin username or password.")

  with tab_staff:
    st.subheader("Staff / Supervisor Sign In")
    st.info("Default Staff credentials: username `staff` | password `staff123`")
    with st.form("staff_sign_in_form"):
      stf_user = st.text_input("Staff Username", value="staff").strip()
      stf_pass = st.text_input("Staff Password", type="password").strip()
      if st.form_submit_button("Sign In as Staff", type="primary"):
        auth = authenticate_user(pg_engine, stf_user, stf_pass)
        if auth:
          st.session_state.farm_user = auth
          st.success(f"Welcome, {auth['full_name']}!")
          st.rerun()
        else:
          st.error("Invalid username or password.")


if st.session_state.farm_user is None:
  render_sign_in()
  st.stop()

current_user = st.session_state.farm_user
is_admin = current_user["role"] == "admin"

st.title("🐄 Animal Farm Management System")
st.caption(
    f"Signed in as **{current_user['full_name']}** (`{current_user['role'].upper()}`) — "
    "Livestock registry, breeding, feed/mortality/death, health, products & performance, inventory, sales/P&L, and worker/farm loans."
)

df_animals = read_df(pg_engine, "SELECT * FROM animals")
df_feed = read_df(pg_engine, "SELECT * FROM feed_and_mortality")
df_health = read_df(pg_engine, "SELECT * FROM health_logs")
df_inv_sales = read_df(pg_engine, "SELECT * FROM inventory_and_sales")
df_products = read_df(pg_engine, "SELECT * FROM animal_products")
df_workers = read_df(pg_engine, "SELECT * FROM workers")
df_w_logs = read_df(pg_engine, "SELECT * FROM worker_finance_logs")
df_farm_loans = read_df(pg_engine, "SELECT * FROM farm_loans")

total_animals = len(df_animals)
total_animal_cost = (
    float(df_animals["cost"].fillna(0).sum()) if not df_animals.empty else 0.0
)
total_feed_other_exp = (
    float(
        (df_feed["total_cost"].fillna(0) + df_feed["other_expenses"].fillna(0))
        .sum()
    )
    if not df_feed.empty
    else 0.0
)
total_vet_exp = (
    float(df_health["vet_cost"].fillna(0).sum()) if not df_health.empty else 0.0
)
total_wages_paid = (
    float(
        df_w_logs[df_w_logs["action_type"] == "Wage Paid"]["amount"]
        .fillna(0)
        .sum()
    )
    if not df_w_logs.empty
    else 0.0
)
total_sales = (
    float(
        df_inv_sales[df_inv_sales["record_type"] == "Sale"]["total_amount"]
        .fillna(0)
        .sum()
    )
    if not df_inv_sales.empty
    else 0.0
)
total_inventory_val = (
    float(
        df_inv_sales[df_inv_sales["record_type"] == "Inventory"]["total_amount"]
        .fillna(0)
        .sum()
    )
    if not df_inv_sales.empty
    else 0.0
)
total_expenses = (
    total_animal_cost + total_feed_other_exp + total_vet_exp + total_wages_paid
)
net_profit_or_loss = total_sales - total_expenses

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Animals", total_animals)
k2.metric("Inventory Value", f"{total_inventory_val:,.2f}")
k3.metric("Total Sales", f"{total_sales:,.2f}")
k4.metric("Total Expenses", f"{total_expenses:,.2f}")
k5.metric(
    "Net Profit / (Loss)",
    f"{net_profit_or_loss:,.2f}",
    delta=f"{net_profit_or_loss:,.2f}",
)

st.sidebar.markdown(f"**User:** {current_user['full_name']}")
st.sidebar.markdown(f"**Role:** `{current_user['role'].upper()}`")
if use_postgres(pg_engine):
  st.sidebar.success(f"🟢 {db_status_msg}")
else:
  st.sidebar.warning(f"🟡 {db_status_msg}")

if st.sidebar.button("🚪 Sign Out"):
  st.session_state.farm_user = None
  st.rerun()

nav_sections = [
    "🐾 Animals & Categories",
    "🥛 Animal Products & Performance",
    "🌾 Feed, Mortality, Death & Days",
    "🩺 Health & Medication",
    "📦 Inventory, Planning & Sales/P&L",
    "👷 Workers: Pay, Credit & Loans",
    "🏦 Farm Loans Taken",
]
if is_admin:
  nav_sections.append("🛡️ Admin User & Password Control")

if st.session_state.nav_section not in nav_sections:
  st.session_state.nav_section = nav_sections[0]

nav = st.sidebar.radio("Farm Sections", nav_sections, key="nav_section")

# ---------------------------------------------------------
# 1. ANIMALS REGISTERED + UNIFORM PICTURES + DIRECT ENTRY ON CLICK
# ---------------------------------------------------------
if nav == "🐾 Animals & Categories":
  st.subheader("🐾 Click Any Animal Picture to Jump Directly to Its Entry Form")
  st.caption(
      "All animal pictures have uniform size. Clicking an animal opens its entry "
      "point right below with that animal category pre-selected."
  )

  gallery_cols = st.columns(4)
  for idx, cat in enumerate(ANIMAL_CATEGORIES):
    with gallery_cols[idx % 4]:
      render_uniform_image(ANIMAL_IMAGES[cat], caption=cat, hero=False)
      btn_label = (
          f"✅ {cat} (Selected)"
          if st.session_state.selected_animal_type == cat
          else f"Enter {cat}"
      )
      if st.button(btn_label, key=f"img_jump_{idx}", use_container_width=True):
        st.session_state.selected_animal_type = cat
        st.rerun()

  active_cat = st.session_state.selected_animal_type
  if active_cat not in ANIMAL_CATEGORIES:
    active_cat = ANIMAL_CATEGORIES[0]

  st.markdown("---")
  st.subheader(f"✍️ Direct Entry Point — {active_cat}")
  entry_cols = st.columns([1, 2])
  with entry_cols[0]:
    render_uniform_image(
        ANIMAL_IMAGES[active_cat],
        caption=f"Active Entry: {active_cat}",
        hero=True,
    )
  with entry_cols[1]:
    st.markdown(f"### Register {active_cat}")
    st.write(
        "All fields are optional—fill in whatever details you have and save "
        "directly into your farm records."
    )

  with st.form(f"register_animal_form_{active_cat}", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    animal_type = c1.selectbox(
        "Animal Type",
        ANIMAL_CATEGORIES,
        index=ANIMAL_CATEGORIES.index(active_cat),
    )
    room_number = c2.text_input(
        "Animal Room / Pen Number (optional)", placeholder="Pen-01"
    ).strip()
    id_number = c3.text_input(
        "ID Number (optional)", placeholder="ANM-101"
    ).strip()
    sex = c4.selectbox("Sex", ["Female", "Male", "Mixed Batch"])

    c5, c6, c7, c8 = st.columns(4)
    date_brought = c5.date_input("Date Brought", value=date.today())
    cost = c6.number_input("Animal Cost", min_value=0.0, step=10.0)
    date_of_birth = c7.date_input("Date of Birth", value=date.today())
    crossing_date = c8.date_input("Crossing Date (optional)", value=date.today())

    c9, c10, c11 = st.columns(3)
    farrow_date = c9.date_input(
        "Farrow / Birth Date (optional)", value=date.today()
    )
    plan_buy_date = c10.date_input("Planning to Buy Time", value=date.today())
    plan_sell_date = c11.date_input("Planning to Sell Time", value=date.today())

    if st.form_submit_button(f"Save {animal_type} Record", type="primary"):
      final_id = id_number if id_number else f"ANM-{uuid.uuid4().hex[:6].upper()}"
      final_room = room_number if room_number else "Unassigned"
      st.session_state.selected_animal_type = animal_type
      try:
        exec_sql(
            pg_engine,
            """
                        INSERT INTO animals (
                            id_number, animal_type, room_number, date_brought,
                            sex, cost, date_of_birth, crossing_date, farrow_date,
                            plan_buy_date, plan_sell_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
            (
                final_id,
                animal_type,
                final_room,
                str(date_brought),
                sex,
                float(cost),
                str(date_of_birth),
                str(crossing_date),
                str(farrow_date),
                str(plan_buy_date),
                str(plan_sell_date),
            ),
        )
        st.success(
            f"Registered {animal_type} with ID `{final_id}` in `{final_room}`."
        )
        st.rerun()
      except Exception as exc:
        st.error(f"Could not save animal record: {exc}")

  st.markdown("---")
  st.subheader("📊 Totals by Animal Category")
  df_animals = read_df(pg_engine, "SELECT * FROM animals")
  if not df_animals.empty:
    cat_summary = (
        df_animals.groupby("animal_type")
        .agg(
            Total_Animals=("id_number", "count"),
            Total_Animal_Cost=("cost", "sum"),
        )
        .reset_index()
    )
    st.dataframe(cat_summary, use_container_width=True, hide_index=True)

    st.subheader("📋 Registered Animals Directory")
    st.dataframe(df_animals, use_container_width=True, hide_index=True)
  else:
    st.info("No animals registered yet.")

# ---------------------------------------------------------
# 2. ANIMAL PRODUCTS & PERFORMANCE BY ANIMAL ID
# ---------------------------------------------------------
elif nav == "🥛 Animal Products & Performance":
  st.subheader("🥛 Animal Products Total & Performance by Animal ID")
  st.caption(
      "Track milk volume, eggs laid, total chicks, chicks born by a specific "
      "animal ID, and birth given—linked to each Animal ID so you can see "
      "which animals are performing best and which need attention."
  )

  registered_ids = (
      df_animals["id_number"].dropna().astype(str).tolist()
      if not df_animals.empty and "id_number" in df_animals.columns
      else []
  )

  with st.form("animal_products_form", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    if registered_ids:
      chosen_existing_id = c1.selectbox(
          "Select Registered Animal ID", ["Custom / Type Below"] + registered_ids
      )
    else:
      chosen_existing_id = c1.selectbox(
          "Select Registered Animal ID", ["Custom / Type Below"]
      )
    typed_animal_id = c2.text_input(
        "Animal ID Number (Type / Override)", placeholder="e.g., COW-01 / HEN-12 / SOW-03"
    ).strip()
    prod_animal_type = c3.selectbox("Animal Type", ANIMAL_CATEGORIES)
    prod_room = c4.text_input("Room / Pen Number (optional)", placeholder="Pen-01").strip()

    c5, c6, c7 = st.columns(3)
    prod_category = c5.selectbox(
        "Product / Output Type",
        [
            "Milk Volume",
            "Eggs Laid",
            "Total Chicks",
            "Chicks Birth by Animal ID",
            "Birth Given (Offspring / Litter / Kids / Calves)",
            "Other Animal Product",
        ],
    )
    prod_detail = c6.text_input(
        "Product / Birth Details (optional)",
        placeholder="e.g., Morning milking, crate of eggs, batch #4, 6 piglets born",
    ).strip()
    unit_label = c7.text_input(
        "Unit (optional)", placeholder="e.g., Litres, Eggs, Chicks, Offspring"
    ).strip()

    prod_qty = quantity_selector(
        "Product Quantity / Volume / Count",
        "prod_qty",
        default_preset=1,
        min_val=0.0,
        step=1.0,
    )

    c8, c9 = st.columns(2)
    prod_date = c8.date_input("Date Recorded", value=date.today())
    prod_notes = c9.text_input(
        "Performance / Health Notes (optional)",
        placeholder="e.g., Strong yield / low output / needs checkup",
    ).strip()

    if st.form_submit_button("Save Animal Product Record", type="primary"):
      final_animal_id = (
          typed_animal_id
          if typed_animal_id
          else (
              chosen_existing_id
              if chosen_existing_id != "Custom / Type Below"
              else f"ID-{uuid.uuid4().hex[:5].upper()}"
          )
      )
      default_unit = unit_label
      if not default_unit:
        if prod_category == "Milk Volume":
          default_unit = "Litres"
        elif prod_category == "Eggs Laid":
          default_unit = "Eggs"
        elif "Chicks" in prod_category:
          default_unit = "Chicks"
        elif "Birth Given" in prod_category:
          default_unit = "Births / Offspring"
        else:
          default_unit = "Units"

      exec_sql(
          pg_engine,
          """
                INSERT INTO animal_products (
                    animal_id, animal_type, room_number, product_category,
                    product_detail, quantity, unit_label, record_date, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
          (
              final_animal_id,
              prod_animal_type,
              prod_room or "General",
              prod_category,
              prod_detail or prod_category,
              float(prod_qty),
              default_unit,
              str(prod_date),
              prod_notes,
          ),
      )
      st.success(
          f"Recorded {prod_qty:g} {default_unit} ({prod_category}) for Animal ID `{final_animal_id}`."
      )
      st.rerun()

  df_prod_all = read_df(pg_engine, "SELECT * FROM animal_products ORDER BY id DESC")

  st.markdown("---")
  st.subheader("📦 Farm-Wide Product Totals")
  if not df_prod_all.empty:
    milk_tot = float(
        df_prod_all[df_prod_all["product_category"] == "Milk Volume"]["quantity"]
        .fillna(0)
        .sum()
    )
    eggs_tot = float(
        df_prod_all[df_prod_all["product_category"] == "Eggs Laid"]["quantity"]
        .fillna(0)
        .sum()
    )
    chicks_tot = float(
        df_prod_all[
            df_prod_all["product_category"].isin(
                ["Total Chicks", "Chicks Birth by Animal ID"]
            )
        ]["quantity"]
        .fillna(0)
        .sum()
    )
    births_tot = float(
        df_prod_all[
            df_prod_all["product_category"].isin(
                [
                    "Birth Given (Offspring / Litter / Kids / Calves)",
                    "Chicks Birth by Animal ID",
                ]
            )
        ]["quantity"]
        .fillna(0)
        .sum()
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Milk Volume", f"{milk_tot:,.2f}")
    m2.metric("Total Eggs Laid", f"{eggs_tot:,.0f}")
    m3.metric("Total Chicks (All / Born)", f"{chicks_tot:,.0f}")
    m4.metric("Total Births / Chicks Born", f"{births_tot:,.0f}")

    st.markdown("---")
    st.subheader("🏆 Performance by Animal ID (Who Is Doing Well vs. Not)")

    perf_rows = []
    for aid, grp in df_prod_all.groupby("animal_id"):
      a_types = ", ".join(sorted(grp["animal_type"].dropna().unique().tolist()))
      milk_v = float(
          grp[grp["product_category"] == "Milk Volume"]["quantity"]
          .fillna(0)
          .sum()
      )
      eggs_v = float(
          grp[grp["product_category"] == "Eggs Laid"]["quantity"]
          .fillna(0)
          .sum()
      )
      chicks_v = float(
          grp[
              grp["product_category"].isin(
                  ["Total Chicks", "Chicks Birth by Animal ID"]
              )
          ]["quantity"]
          .fillna(0)
          .sum()
      )
      births_v = float(
          grp[
              grp["product_category"].isin(
                  [
                      "Birth Given (Offspring / Litter / Kids / Calves)",
                      "Chicks Birth by Animal ID",
                  ]
              )
          ]["quantity"]
          .fillna(0)
          .sum()
      )
      other_v = float(
          grp[grp["product_category"] == "Other Animal Product"]["quantity"]
          .fillna(0)
          .sum()
      )
      total_out = milk_v + eggs_v + chicks_v + births_v + other_v
      entries_cnt = len(grp)

      # Check mortality/death linked to this ID if present in feed_and_mortality
      mort_linked = 0
      if not df_feed.empty and "id_number" in df_feed.columns:
        m_sub = df_feed[
            df_feed["id_number"].astype(str).str.lower() == str(aid).lower()
        ]
        if not m_sub.empty:
          mort_linked = int(
              m_sub["mortality_count"].fillna(0).sum()
              + m_sub["death_count"].fillna(0).sum()
          )

      if total_out > 0 and mort_linked == 0:
        status_badge = "🟢 Doing Well"
      elif total_out > 0 and mort_linked > 0:
        status_badge = "🟡 Moderate (Watch Losses)"
      else:
        status_badge = "🔴 Low / No Output Yet"

      perf_rows.append({
          "Animal ID": aid,
          "Animal Type": a_types,
          "Milk Volume": milk_v,
          "Eggs Laid": eggs_v,
          "Chicks (Total / Born)": chicks_v,
          "Birth Given": births_v,
          "Other Output": other_v,
          "Total Output Units": total_out,
          "Linked Losses": mort_linked,
          "Records": entries_cnt,
          "Performance Status": status_badge,
      })

    df_perf = pd.DataFrame(perf_rows).sort_values(
        by="Total Output Units", ascending=False
    )
    st.dataframe(df_perf, use_container_width=True, hide_index=True)

    st.subheader("🔎 Inspect a Specific Animal ID's Product History")
    selected_inspect_id = st.selectbox(
        "Filter Product Logs by Animal ID",
        ["All Animal IDs"] + df_perf["Animal ID"].tolist(),
    )
    if selected_inspect_id != "All Animal IDs":
      st.dataframe(
          df_prod_all[df_prod_all["animal_id"] == selected_inspect_id],
          use_container_width=True,
          hide_index=True,
      )
    else:
      st.dataframe(df_prod_all, use_container_width=True, hide_index=True)
  else:
    st.info(
        "No animal product records yet. Add milk volume, eggs laid, chicks, or "
        "birth records above to track each Animal ID."
    )

# ---------------------------------------------------------
# 3. FEED, SEPARATE MORTALITY vs DEATH, QUANTITY DROPDOWN + TYPE, "OF WHAT?"
# ---------------------------------------------------------
elif nav == "🌾 Feed, Mortality, Death & Days":
  st.subheader(
      "🌾 Feed / Food, Separate Mortality & Death, Days Spent & Days Left"
  )
  st.caption(
      "No fields are required. Select or type quantities, specify 'of what?', "
      "and log mortality separately from death."
  )

  with st.form("feed_mortality_form", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    a_type = c1.selectbox("Animal Type", ANIMAL_CATEGORIES)
    room_no = c2.text_input(
        "Animal Room Number (optional)", placeholder="Pen-01"
    ).strip()
    anim_id = c3.text_input("Animal / Batch ID Number (optional)").strip()
    feed_type = c4.text_input(
        "Feed Type (optional)", placeholder="Starter Mash"
    ).strip()

    c5, c6, c7 = st.columns(3)
    food_type = c5.text_input(
        "Food Type / Supplement (optional)", placeholder="Cassava / Maize"
    ).strip()
    food_of_what = c6.text_input(
        "Food Type Quantity — of what? (optional)",
        placeholder="e.g., 50kg bags of maize, crates, buckets",
    ).strip()
    other_exp = c7.number_input(
        "Other Expenses (optional)", min_value=0.0, step=1.0
    )

    st.markdown(
        "**Quantity & Unit Cost (Dropdown quick select + exact typed number)**"
    )
    qty = quantity_selector(
        "Quantity", "feed_qty", default_preset=10, min_val=0.0, step=1.0
    )
    unit_cost = quantity_selector(
        "Price / Cost per Unit",
        "feed_unit_cost",
        default_preset=10,
        min_val=0.0,
        step=1.0,
    )

    st.markdown("---")
    st.markdown("**Separate Mortality & Death Tracking**")
    m_col1, m_col2, m_col3 = st.columns(3)
    mort_cnt = int(
        quantity_selector(
            "Mortality Count", "mort_cnt", default_preset=1, min_val=0.0, step=1.0
        )
    )
    mort_of_what = m_col1.text_input(
        "Mortality — of what? (optional)",
        placeholder="e.g., piglets, chicks, batch #2",
    ).strip()
    mort_date = m_col2.date_input("Date of Mortality", value=date.today())
    m_col3.write("")

    d_col1, d_col2, d_col3 = st.columns(3)
    death_cnt = int(
        quantity_selector(
            "Death Count", "death_cnt", default_preset=1, min_val=0.0, step=1.0
        )
    )
    death_of_what = d_col1.text_input(
        "Death — of what? (optional)",
        placeholder="e.g., adult sow, goat kid, culling/accident",
    ).strip()
    death_date = d_col2.date_input("Date of Death", value=date.today())
    d_col3.write("")

    st.markdown("---")
    c9, c10 = st.columns(2)
    date_rec = c9.date_input("Date Recorded / Brought", value=date.today())
    date_fin = c10.date_input("Date Finish (Expected)", value=date.today())

    if st.form_submit_button(
        "Save Feed, Mortality & Death Record", type="primary"
    ):
      computed_total = float(qty) * float(unit_cost)
      exec_sql(
          pg_engine,
          """
                INSERT INTO feed_and_mortality (
                    animal_type, room_number, id_number, feed_type, food_type,
                    food_quantity_of_what, quantity, unit_cost, total_cost,
                    date_recorded, date_finish, mortality_count, mortality_of_what,
                    death_count, death_of_what, date_of_mortality, date_of_death,
                    other_expenses
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
          (
              a_type,
              room_no or "General",
              anim_id,
              feed_type or "Standard Feed",
              food_type or feed_type or "Standard Food",
              food_of_what,
              float(qty),
              float(unit_cost),
              computed_total,
              str(date_rec),
              str(date_fin),
              int(mort_cnt),
              mort_of_what,
              int(death_cnt),
              death_of_what,
              str(mort_date),
              str(death_date),
              float(other_exp),
          ),
      )
      st.success("Feed, mortality, death, and days record saved.")
      st.rerun()

  df_feed = read_df(pg_engine, "SELECT * FROM feed_and_mortality ORDER BY id DESC")
  if not df_feed.empty:
    days_spent_list = []
    days_left_list = []
    for _, r in df_feed.iterrows():
      sp, lf = calc_days_spent_and_left(r["date_recorded"], r["date_finish"])
      days_spent_list.append(sp)
      days_left_list.append(lf)
    df_feed["days_spent"] = days_spent_list
    df_feed["days_left"] = days_left_list
    st.dataframe(df_feed, use_container_width=True, hide_index=True)
  else:
    st.info("No feed, mortality, or death logs yet.")

# ---------------------------------------------------------
# 4. HEALTH, VISIT DATE, DISEASE & ANIMAL MEDICATION
# ---------------------------------------------------------
elif nav == "🩺 Health & Medication":
  st.subheader("🩺 Vet Visits, Diseases & Animal Medication")
  st.caption("No fields are required—leave any field blank if not yet known.")

  with st.form("health_form", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    h_id = c1.text_input(
        "Animal ID Number (optional)", placeholder="ANM-101"
    ).strip()
    h_type = c2.selectbox("Animal Type", ANIMAL_CATEGORIES)
    h_room = c3.text_input(
        "Room Number (optional)", placeholder="Pen-01"
    ).strip()
    visit_dt = c4.date_input("Visit Date", value=date.today())

    c5, c6, c7 = st.columns(3)
    disease = c5.text_input(
        "What Disease / Condition? (optional)",
        placeholder="Swine Fever / Deworming",
    ).strip()
    medication = c6.text_input(
        "Animal Medication Given (optional)", placeholder="Oxytetracycline"
    ).strip()
    vet_cost = c7.number_input(
        "Medication / Visit Cost (optional)", min_value=0.0, step=1.0
    )

    if st.form_submit_button("Save Health Record", type="primary"):
      exec_sql(
          pg_engine,
          """
                INSERT INTO health_logs (
                    id_number, animal_type, room_number, visit_date,
                    disease, medication, vet_cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
          (
              h_id or "General",
              h_type,
              h_room or "General",
              str(visit_dt),
              disease or "Unspecified",
              medication or "None / Pending",
              float(vet_cost),
          ),
      )
      st.success("Health and medication record saved.")
      st.rerun()

  df_health = read_df(pg_engine, "SELECT * FROM health_logs ORDER BY id DESC")
  if not df_health.empty:
    st.dataframe(df_health, use_container_width=True, hide_index=True)
  else:
    st.info("No health or medication records yet.")

# ---------------------------------------------------------
# 5. INVENTORY, PLANNING TO BUY/SELL, SALES & PROFIT/LOSS
# ---------------------------------------------------------
elif nav == "📦 Inventory, Planning & Sales/P&L":
  st.subheader("📦 Inventory, Buy/Sell Planning, Sales & Profit/Loss")
  st.caption(
      "No fields are required—select or type quantities and prices freely."
  )

  with st.form("inv_sales_form", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    rec_type = c1.selectbox("Entry Type", ["Inventory", "Sale"])
    a_type = c2.selectbox("Animal Type", ANIMAL_CATEGORIES)
    anim_id = c3.text_input("Animal / Item ID (optional)").strip()
    item_desc = c4.text_input(
        "Item / Batch Description (optional)",
        placeholder="Grower Pigs / Feed Bags",
    ).strip()

    qty = quantity_selector(
        "Quantity", "inv_qty", default_preset=1, min_val=0.0, step=1.0
    )
    unit_price = quantity_selector(
        "Price per Unit", "inv_price", default_preset=10, min_val=0.0, step=1.0
    )

    c7, c8, c9 = st.columns(3)
    rec_date = c7.date_input("Transaction Date", value=date.today())
    plan_buy = c8.date_input("Planning to Buy Time", value=date.today())
    plan_sell = c9.date_input("Planning to Sell Time", value=date.today())

    if st.form_submit_button("Save Entry", type="primary"):
      total_val = float(qty) * float(unit_price)
      exec_sql(
          pg_engine,
          """
                INSERT INTO inventory_and_sales (
                    record_type, animal_type, id_number, item_or_batch,
                    quantity, unit_price, total_amount, record_date,
                    plan_buy_time, plan_sell_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
          (
              rec_type,
              a_type,
              anim_id,
              item_desc or rec_type,
              float(qty),
              float(unit_price),
              total_val,
              str(rec_date),
              str(plan_buy),
              str(plan_sell),
          ),
      )
      st.success(f"{rec_type} entry saved (Total: {total_val:,.2f}).")
      st.rerun()

  st.markdown("---")
  st.subheader("📈 Profit & Loss Breakdown")
  p1, p2, p3, p4 = st.columns(4)
  p1.metric("Total Sales", f"{total_sales:,.2f}")
  p2.metric("Animal + Feed + Other + Vet Costs", f"{total_expenses:,.2f}")
  p3.metric("Current Inventory Stock Value", f"{total_inventory_val:,.2f}")
  status_label = "PROFIT" if net_profit_or_loss >= 0 else "LOSS"
  p4.metric(f"Net {status_label}", f"{net_profit_or_loss:,.2f}")

  df_inv_sales = read_df(
      pg_engine, "SELECT * FROM inventory_and_sales ORDER BY id DESC"
  )
  if not df_inv_sales.empty:
    st.dataframe(df_inv_sales, use_container_width=True, hide_index=True)
  else:
    st.info("No inventory or sales records yet.")

# ---------------------------------------------------------
# 6. EMPLOY WORKERS: DAILY, WEEKLY, MONTHLY, CREDIT & LOANS
# ---------------------------------------------------------
elif nav == "👷 Workers: Pay, Credit & Loans":
  st.subheader("👷 Workers Registry, Payroll, Credit & Worker Loans")
  st.caption(
      "No fields are required—defaults will be applied if any field is left blank."
  )

  col_reg, col_act = st.columns(2)

  with col_reg:
    st.markdown("#### Register New Worker")
    with st.form("add_worker_form", clear_on_submit=True):
      w_name = st.text_input("Worker Full Name (optional)").strip()
      w_role = st.text_input(
          "Role / Duty (optional)", placeholder="Herdsman / Cleaner"
      ).strip()
      w_cycle = st.selectbox("Pay Schedule", ["Daily", "Weekly", "Monthly"])
      w_rate = quantity_selector(
          "Standard Pay Rate", "w_rate", default_preset=20, min_val=0.0, step=5.0
      )
      if st.form_submit_button("Register Worker", type="primary"):
        final_w_name = (
            w_name if w_name else f"Worker-{uuid.uuid4().hex[:4].upper()}"
        )
        w_id = f"WRK-{uuid.uuid4().hex[:5].upper()}"
        exec_sql(
            pg_engine,
            """
                        INSERT INTO workers (worker_id, full_name, role, pay_cycle, pay_rate, credit_owed, loan_balance)
                        VALUES (?, ?, ?, ?, ?, 0.0, 0.0)
                        """,
            (
                w_id,
                final_w_name,
                w_role or "Farm Worker",
                w_cycle,
                float(w_rate),
            ),
        )
        st.success(f"Registered worker `{final_w_name}` ({w_cycle}).")
        st.rerun()

  with col_act:
    st.markdown("#### Record Pay, Credit or Worker Loan")
    df_w = read_df(pg_engine, "SELECT * FROM workers ORDER BY full_name ASC")
    if not df_w.empty:
      w_map = {
          f"{r['full_name']} ({r['worker_id']}) — {r['pay_cycle']}": r
          for _, r in df_w.iterrows()
      }
      with st.form("worker_action_form", clear_on_submit=True):
        chosen_w_label = st.selectbox("Select Worker", list(w_map.keys()))
        action_type = st.selectbox(
            "Action",
            [
                "Wage Paid",
                "Pay on Credit (Add to Credit Owed)",
                "Settle Credit Owed",
                "Give Loan to Worker",
                "Deduct Loan Repayment from Worker",
            ],
        )
        amt = quantity_selector(
            "Amount", "w_act_amt", default_preset=10, min_val=0.0, step=5.0
        )
        act_date = st.date_input("Date", value=date.today())
        notes = st.text_input("Notes / Remarks (optional)").strip()

        if st.form_submit_button("Apply Worker Action", type="primary"):
          w_row = w_map[chosen_w_label]
          wid = w_row["worker_id"]
          wname = w_row["full_name"]
          cur_credit = float(w_row["credit_owed"] or 0.0)
          cur_loan = float(w_row["loan_balance"] or 0.0)
          val = float(amt)

          if action_type == "Pay on Credit (Add to Credit Owed)":
            cur_credit += val
          elif action_type == "Settle Credit Owed":
            cur_credit = max(0.0, cur_credit - val)
          elif action_type == "Give Loan to Worker":
            cur_loan += val
          elif action_type == "Deduct Loan Repayment from Worker":
            cur_loan = max(0.0, cur_loan - val)

          exec_sql(
              pg_engine,
              "UPDATE workers SET credit_owed = ?, loan_balance = ? WHERE worker_id = ?",
              (cur_credit, cur_loan, wid),
          )
          exec_sql(
              pg_engine,
              """
                            INSERT INTO worker_finance_logs (worker_id, worker_name, action_type, amount, entry_date, notes)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
              (wid, wname, action_type, val, str(act_date), notes),
          )
          st.success(f"Recorded `{action_type}` of {val:,.2f} for {wname}.")
          st.rerun()
    else:
      st.info("Register a worker first to record pay, credit, or loans.")

  st.markdown("---")
  df_w_display = read_df(
      pg_engine, "SELECT * FROM workers ORDER BY full_name ASC"
  )
  if not df_w_display.empty:
    st.subheader("👥 Workers, Credit Owed & Loan Balances")
    st.dataframe(df_w_display, use_container_width=True, hide_index=True)

  df_w_history = read_df(
      pg_engine, "SELECT * FROM worker_finance_logs ORDER BY id DESC"
  )
  if not df_w_history.empty:
    st.subheader("🧾 Worker Pay, Credit & Loan History")
    st.dataframe(df_w_history, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 7. FARM LOANS TAKEN BY THE FARM
# ---------------------------------------------------------
elif nav == "🏦 Farm Loans Taken":
  st.subheader("🏦 Farm Loans Taken & Repayment Tracking")
  st.caption(
      "No fields are required—defaults will be filled if any field is left blank."
  )

  c_new, c_rep = st.columns(2)

  with c_new:
    st.markdown("#### Take a New Farm Loan")
    with st.form("take_loan_form", clear_on_submit=True):
      lender = st.text_input(
          "Lender / Bank / Institution (optional)"
      ).strip()
      principal = quantity_selector(
          "Loan Amount Taken",
          "loan_prin",
          default_preset=100,
          min_val=0.0,
          step=50.0,
      )
      taken_date = st.date_input("Date Taken", value=date.today())
      l_notes = st.text_input("Purpose / Terms (optional)").strip()
      if st.form_submit_button("Record Farm Loan", type="primary"):
        final_lender = lender if lender else "General Lender"
        lid = f"LOAN-{uuid.uuid4().hex[:5].upper()}"
        exec_sql(
            pg_engine,
            """
                        INSERT INTO farm_loans (loan_id, lender_name, principal_amount, amount_paid, balance_due, date_taken, notes)
                        VALUES (?, ?, ?, 0.0, ?, ?, ?)
                        """,
            (
                lid,
                final_lender,
                float(principal),
                float(principal),
                str(taken_date),
                l_notes,
            ),
        )
        st.success(f"Recorded loan `{lid}` from {final_lender}.")
        st.rerun()

  with c_rep:
    st.markdown("#### Record Farm Loan Repayment")
    df_loans_open = read_df(
        pg_engine, "SELECT * FROM farm_loans WHERE balance_due > 0"
    )
    if not df_loans_open.empty:
      loan_opts = {
          f"{r['loan_id']} — {r['lender_name']} (Bal: {r['balance_due']:,.2f})": r
          for _, r in df_loans_open.iterrows()
      }
      with st.form("repay_farm_loan_form", clear_on_submit=True):
        chosen_l = st.selectbox("Select Active Loan", list(loan_opts.keys()))
        repay_amt = quantity_selector(
            "Repayment Amount",
            "loan_repay",
            default_preset=20,
            min_val=0.0,
            step=20.0,
        )
        if st.form_submit_button("Apply Repayment", type="primary"):
          l_row = loan_opts[chosen_l]
          new_paid = float(l_row["amount_paid"] or 0.0) + float(repay_amt)
          new_bal = max(
              0.0, float(l_row["balance_due"] or 0.0) - float(repay_amt)
          )
          exec_sql(
              pg_engine,
              "UPDATE farm_loans SET amount_paid = ?, balance_due = ? WHERE loan_id = ?",
              (new_paid, new_bal, l_row["loan_id"]),
          )
          st.success(f"Updated repayment for `{l_row['loan_id']}`.")
          st.rerun()
    else:
      st.info("No active unpaid farm loans.")

  st.markdown("---")
  df_all_loans = read_df(
      pg_engine, "SELECT * FROM farm_loans ORDER BY date_taken DESC"
  )
  if not df_all_loans.empty:
    st.dataframe(df_all_loans, use_container_width=True, hide_index=True)
  else:
    st.info("No farm loans recorded yet.")

# ---------------------------------------------------------
# 8. ADMIN USER & PASSWORD CONTROL
# ---------------------------------------------------------
elif nav == "🛡️ Admin User & Password Control":
  if not is_admin:
    st.error("Administrator access required.")
    st.stop()

  st.subheader("🛡️ Admin User Management & Password Reset")
  df_users = read_df(
      pg_engine, "SELECT id, username, full_name, role FROM users ORDER BY id ASC"
  )
  st.dataframe(df_users, use_container_width=True, hide_index=True)

  c_add, c_pwd = st.columns(2)
  with c_add:
    st.markdown("#### Create New User Account")
    with st.form("create_farm_user_form", clear_on_submit=True):
      u_name = st.text_input("Username (optional)").strip()
      u_full = st.text_input("Full Name (optional)").strip()
      u_role = st.selectbox("Role", ["staff", "admin"])
      u_pass = st.text_input(
          "Initial Password (optional)", type="password"
      ).strip()
      if st.form_submit_button("Create Account", type="primary"):
        final_u = u_name if u_name else f"user_{uuid.uuid4().hex[:4]}"
        final_full = u_full if u_full else final_u
        final_pass = u_pass if u_pass else "changeme123"
        try:
          exec_sql(
              pg_engine,
              "INSERT INTO users (username, full_name, role, password) VALUES (?, ?, ?, ?)",
              (final_u, final_full, u_role, final_pass),
          )
          st.success(f"Created {u_role} account `{final_u}`.")
          st.rerun()
        except Exception as exc:
          st.error(f"Could not create user: {exc}")

  with c_pwd:
    st.markdown("#### Reset User Password")
    if not df_users.empty:
      with st.form("reset_farm_user_pwd_form", clear_on_submit=True):
        target_u = st.selectbox("Select User", df_users["username"].tolist())
        new_p = st.text_input("New Password", type="password").strip()
        if st.form_submit_button("Update Password", type="primary"):
          final_new_p = new_p if new_p else "changeme123"
          exec_sql(
              pg_engine,
              "UPDATE users SET password = ? WHERE username = ?",
              (final_new_p, target_u),
          )
          st.success(f"Password updated for `{target_u}`.")
          st.rerun()
