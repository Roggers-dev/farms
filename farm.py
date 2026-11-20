from datetime import date, datetime
import sqlite3
import uuid
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Animal Farm Management System",
    page_icon="🐄",
    layout="wide",
)

DB_PATH = "animal_farm_management.db"

ANIMAL_CATEGORIES = [
    "Pigs / Swine",
    "Poultry (Broilers / Layers)",
    "Cattle",
    "Goats",
    "Sheep",
    "Rabbits",
    "Other Livestock",
]


def init_db():
  with sqlite3.connect(DB_PATH) as conn:
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
                quantity REAL DEFAULT 0.0,
                unit_cost REAL DEFAULT 0.0,
                total_cost REAL DEFAULT 0.0,
                date_recorded TEXT NOT NULL,
                date_finish TEXT,
                mortality_count INTEGER DEFAULT 0,
                date_of_mortality TEXT,
                other_expenses REAL DEFAULT 0.0
            )
        """)
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

    # Seed default Admin and Staff accounts if not present
    conn.execute("""
            INSERT OR IGNORE INTO users (username, full_name, role, password)
            VALUES ('admin', 'Farm Administrator', 'admin', 'admin123')
        """)
    conn.execute("""
            INSERT OR IGNORE INTO users (username, full_name, role, password)
            VALUES ('staff', 'Farm Supervisor', 'staff', 'staff123')
        """)


def read_df(query, params=()):
  with sqlite3.connect(DB_PATH) as conn:
    return pd.read_sql(query, conn, params=params)


def exec_sql(query, params=()):
  with sqlite3.connect(DB_PATH) as conn:
    conn.execute(query, params)
    conn.commit()


def authenticate_user(username, password):
  df = read_df(
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


init_db()

if "farm_user" not in st.session_state:
  st.session_state.farm_user = None


def render_sign_in():
  st.title("🐄 Animal Farm Management System — Sign In")
  st.caption(
      "Sign in with your Admin or Staff credentials to manage livestock, feed, "
      "health, inventory, sales, workers, and loans."
  )

  tab_admin, tab_staff = st.tabs(["🛡️ Admin Sign In", "👤 Staff Sign In"])

  with tab_admin:
    st.subheader("Administrator Sign In")
    st.info("Default Admin credentials: username `admin` | password `admin123`")
    with st.form("admin_sign_in_form"):
      adm_user = st.text_input("Admin Username", value="admin").strip()
      adm_pass = st.text_input("Admin Password", type="password").strip()
      if st.form_submit_button("Sign In as Admin", type="primary"):
        auth = authenticate_user(adm_user, adm_pass)
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
        auth = authenticate_user(stf_user, stf_pass)
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
    "Livestock registry, breeding, feed/mortality, health, inventory, sales/P&L, and worker/farm loans."
)

# Top Executive Overview Bar
df_animals = read_df("SELECT * FROM animals")
df_feed = read_df("SELECT * FROM feed_and_mortality")
df_health = read_df("SELECT * FROM health_logs")
df_inv_sales = read_df("SELECT * FROM inventory_and_sales")
df_workers = read_df("SELECT * FROM workers")
df_w_logs = read_df("SELECT * FROM worker_finance_logs")
df_farm_loans = read_df("SELECT * FROM farm_loans")

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
if st.sidebar.button("🚪 Sign Out"):
  st.session_state.farm_user = None
  st.rerun()

nav_sections = [
    "🐾 Animals & Categories",
    "🌾 Feed, Mortality & Days",
    "🩺 Health & Medication",
    "📦 Inventory, Planning & Sales/P&L",
    "👷 Workers: Pay, Credit & Loans",
    "🏦 Farm Loans Taken",
]
if is_admin:
  nav_sections.append("🛡️ Admin User & Password Control")

nav = st.sidebar.radio("Farm Sections", nav_sections)

# ---------------------------------------------------------
# 1. ANIMALS REGISTERED & CATEGORY TOTALS
# ---------------------------------------------------------
if nav == "🐾 Animals & Categories":
  st.subheader("🐾 Register Animals & Category Totals")

  with st.form("register_animal_form", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    animal_type = c1.selectbox("Animal Type", ANIMAL_CATEGORIES)
    room_number = c2.text_input("Animal Room / Pen Number", placeholder="Pen-01").strip()
    id_number = c3.text_input(
        "ID Number (leave blank for auto ID)", placeholder="ANM-101"
    ).strip()
    sex = c4.selectbox("Sex", ["Female", "Male", "Mixed Batch"])

    c5, c6, c7, c8 = st.columns(4)
    date_brought = c5.date_input("Date Brought", value=date.today())
    cost = c6.number_input("Animal Cost", min_value=0.0, step=10.0)
    date_of_birth = c7.date_input("Date of Birth", value=date.today())
    crossing_date = c8.date_input("Crossing Date (optional)", value=date.today())

    c9, c10, c11 = st.columns(3)
    farrow_date = c9.date_input("Farrow / Birth Date (optional)", value=date.today())
    plan_buy_date = c10.date_input("Planning to Buy Time", value=date.today())
    plan_sell_date = c11.date_input("Planning to Sell Time", value=date.today())

    if st.form_submit_button("Save Animal Record", type="primary"):
      final_id = id_number if id_number else f"ANM-{uuid.uuid4().hex[:6].upper()}"
      if not room_number:
        st.warning("Please enter the Animal Room / Pen Number.")
      else:
        try:
          exec_sql(
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
                  room_number,
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
          st.success(f"Registered {animal_type} with ID `{final_id}` in `{room_number}`.")
          st.rerun()
        except sqlite3.IntegrityError:
          st.error(f"ID Number `{final_id}` already exists. Use a unique ID.")

  st.markdown("---")
  st.subheader("📊 Totals by Animal Category")
  df_animals = read_df("SELECT * FROM animals")
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
# 2. FEED, MORTALITY / DEATH, DAYS SPENT / LEFT & EXPENSES
# ---------------------------------------------------------
elif nav == "🌾 Feed, Mortality & Days":
  st.subheader("🌾 Feed / Food, Mortality, Days Spent & Days Left")

  with st.form("feed_mortality_form", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    a_type = c1.selectbox("Animal Type", ANIMAL_CATEGORIES)
    room_no = c2.text_input("Animal Room Number", placeholder="Pen-01").strip()
    anim_id = c3.text_input("Animal / Batch ID Number (optional)").strip()
    feed_type = c4.text_input("Feed Type", placeholder="Starter Mash").strip()

    c5, c6, c7, c8 = st.columns(4)
    food_type = c5.text_input("Food Type / Supplement", placeholder="Cassava / Maize").strip()
    qty = c6.number_input("Quantity", min_value=0.0, step=1.0)
    unit_cost = c7.number_input("Price / Cost per Unit", min_value=0.0, step=1.0)
    other_exp = c8.number_input("Other Expenses", min_value=0.0, step=1.0)

    c9, c10, c11, c12 = st.columns(4)
    date_rec = c9.date_input("Date Recorded / Brought", value=date.today())
    date_fin = c10.date_input("Date Finish (Expected)", value=date.today())
    mort_cnt = c11.number_input("Mortality / Death Count", min_value=0, step=1)
    mort_date = c12.date_input("Date of Mortality / Death", value=date.today())

    if st.form_submit_button("Save Feed & Mortality Record", type="primary"):
      computed_total = float(qty) * float(unit_cost)
      exec_sql(
          """
                INSERT INTO feed_and_mortality (
                    animal_type, room_number, id_number, feed_type, food_type,
                    quantity, unit_cost, total_cost, date_recorded, date_finish,
                    mortality_count, date_of_mortality, other_expenses
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
          (
              a_type,
              room_no or "General",
              anim_id,
              feed_type or "Standard Feed",
              food_type or feed_type or "Standard Food",
              float(qty),
              float(unit_cost),
              computed_total,
              str(date_rec),
              str(date_fin),
              int(mort_cnt),
              str(mort_date),
              float(other_exp),
          ),
      )
      st.success("Feed, days & mortality record saved.")
      st.rerun()

  df_feed = read_df("SELECT * FROM feed_and_mortality ORDER BY id DESC")
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
    st.info("No feed or mortality logs yet.")

# ---------------------------------------------------------
# 3. HEALTH, VISIT DATE, DISEASE & ANIMAL MEDICATION
# ---------------------------------------------------------
elif nav == "🩺 Health & Medication":
  st.subheader("🩺 Vet Visits, Diseases & Animal Medication")

  with st.form("health_form", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    h_id = c1.text_input("Animal ID Number", placeholder="ANM-101").strip()
    h_type = c2.selectbox("Animal Type", ANIMAL_CATEGORIES)
    h_room = c3.text_input("Room Number", placeholder="Pen-01").strip()
    visit_dt = c4.date_input("Visit Date", value=date.today())

    c5, c6, c7 = st.columns(3)
    disease = c5.text_input("What Disease / Condition?", placeholder="Swine Fever / Deworming").strip()
    medication = c6.text_input("Animal Medication Given", placeholder="Oxytetracycline").strip()
    vet_cost = c7.number_input("Medication / Visit Cost", min_value=0.0, step=1.0)

    if st.form_submit_button("Save Health Record", type="primary"):
      if not h_id or not disease or not medication:
        st.warning("Please fill in Animal ID, Disease, and Medication.")
      else:
        exec_sql(
            """
                    INSERT INTO health_logs (
                        id_number, animal_type, room_number, visit_date,
                        disease, medication, vet_cost
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
            (
                h_id,
                h_type,
                h_room or "General",
                str(visit_dt),
                disease,
                medication,
                float(vet_cost),
            ),
        )
        st.success("Health and medication record saved.")
        st.rerun()

  df_health = read_df("SELECT * FROM health_logs ORDER BY id DESC")
  if not df_health.empty:
    st.dataframe(df_health, use_container_width=True, hide_index=True)
  else:
    st.info("No health or medication records yet.")

# ---------------------------------------------------------
# 4. INVENTORY, PLANNING TO BUY/SELL, SALES & PROFIT/LOSS
# ---------------------------------------------------------
elif nav == "📦 Inventory, Planning & Sales/P&L":
  st.subheader("📦 Inventory, Buy/Sell Planning, Sales & Profit/Loss")

  with st.form("inv_sales_form", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    rec_type = c1.selectbox("Entry Type", ["Inventory", "Sale"])
    a_type = c2.selectbox("Animal Type", ANIMAL_CATEGORIES)
    anim_id = c3.text_input("Animal / Item ID (optional)").strip()
    item_desc = c4.text_input("Item / Batch Description", placeholder="Grower Pigs / Feed Bags").strip()

    c5, c6, c7 = st.columns(3)
    qty = c5.number_input("Quantity", min_value=0.1, value=1.0, step=1.0)
    unit_price = c6.number_input("Price per Unit", min_value=0.0, step=1.0)
    rec_date = c7.date_input("Transaction Date", value=date.today())

    c8, c9 = st.columns(2)
    plan_buy = c8.date_input("Planning to Buy Time", value=date.today())
    plan_sell = c9.date_input("Planning to Sell Time", value=date.today())

    if st.form_submit_button("Save Entry", type="primary"):
      total_val = float(qty) * float(unit_price)
      exec_sql(
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

  df_inv_sales = read_df("SELECT * FROM inventory_and_sales ORDER BY id DESC")
  if not df_inv_sales.empty:
    st.dataframe(df_inv_sales, use_container_width=True, hide_index=True)
  else:
    st.info("No inventory or sales records yet.")

# ---------------------------------------------------------
# 5. EMPLOY WORKERS: DAILY, WEEKLY, MONTHLY, CREDIT & LOANS
# ---------------------------------------------------------
elif nav == "👷 Workers: Pay, Credit & Loans":
  st.subheader("👷 Workers Registry, Payroll, Credit & Worker Loans")

  col_reg, col_act = st.columns(2)

  with col_reg:
    st.markdown("#### Register New Worker")
    with st.form("add_worker_form", clear_on_submit=True):
      w_name = st.text_input("Worker Full Name").strip()
      w_role = st.text_input("Role / Duty", placeholder="Herdsman / Cleaner").strip()
      w_cycle = st.selectbox("Pay Schedule", ["Daily", "Weekly", "Monthly"])
      w_rate = st.number_input("Standard Pay Rate", min_value=0.0, step=5.0)
      if st.form_submit_button("Register Worker", type="primary"):
        if not w_name:
          st.warning("Enter worker full name.")
        else:
          w_id = f"WRK-{uuid.uuid4().hex[:5].upper()}"
          exec_sql(
              """
                            INSERT INTO workers (worker_id, full_name, role, pay_cycle, pay_rate, credit_owed, loan_balance)
                            VALUES (?, ?, ?, ?, ?, 0.0, 0.0)
                            """,
              (w_id, w_name, w_role or "Farm Worker", w_cycle, float(w_rate)),
          )
          st.success(f"Registered worker `{w_name}` ({w_cycle}).")
          st.rerun()

  with col_act:
    st.markdown("#### Record Pay, Credit or Worker Loan")
    df_w = read_df("SELECT * FROM workers ORDER BY full_name ASC")
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
        amt = st.number_input("Amount", min_value=0.01, step=5.0)
        act_date = st.date_input("Date", value=date.today())
        notes = st.text_input("Notes / Remarks").strip()

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
              "UPDATE workers SET credit_owed = ?, loan_balance = ? WHERE worker_id = ?",
              (cur_credit, cur_loan, wid),
          )
          exec_sql(
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
  df_w_display = read_df("SELECT * FROM workers ORDER BY full_name ASC")
  if not df_w_display.empty:
    st.subheader("👥 Workers, Credit Owed & Loan Balances")
    st.dataframe(df_w_display, use_container_width=True, hide_index=True)

  df_w_history = read_df("SELECT * FROM worker_finance_logs ORDER BY id DESC")
  if not df_w_history.empty:
    st.subheader("🧾 Worker Pay, Credit & Loan History")
    st.dataframe(df_w_history, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 6. FARM LOANS TAKEN BY THE FARM
# ---------------------------------------------------------
elif nav == "🏦 Farm Loans Taken":
  st.subheader("🏦 Farm Loans Taken & Repayment Tracking")

  c_new, c_rep = st.columns(2)

  with c_new:
    st.markdown("#### Take a New Farm Loan")
    with st.form("take_loan_form", clear_on_submit=True):
      lender = st.text_input("Lender / Bank / Institution").strip()
      principal = st.number_input("Loan Amount Taken", min_value=0.01, step=50.0)
      taken_date = st.date_input("Date Taken", value=date.today())
      l_notes = st.text_input("Purpose / Terms").strip()
      if st.form_submit_button("Record Farm Loan", type="primary"):
        if not lender:
          st.warning("Please enter the lender name.")
        else:
          lid = f"LOAN-{uuid.uuid4().hex[:5].upper()}"
          exec_sql(
              """
                            INSERT INTO farm_loans (loan_id, lender_name, principal_amount, amount_paid, balance_due, date_taken, notes)
                            VALUES (?, ?, ?, 0.0, ?, ?, ?)
                            """,
              (lid, lender, float(principal), float(principal), str(taken_date), l_notes),
          )
          st.success(f"Recorded loan `{lid}` from {lender}.")
          st.rerun()

  with c_rep:
    st.markdown("#### Record Farm Loan Repayment")
    df_loans_open = read_df("SELECT * FROM farm_loans WHERE balance_due > 0")
    if not df_loans_open.empty:
      loan_opts = {
          f"{r['loan_id']} — {r['lender_name']} (Bal: {r['balance_due']:,.2f})": r
          for _, r in df_loans_open.iterrows()
      }
      with st.form("repay_farm_loan_form", clear_on_submit=True):
        chosen_l = st.selectbox("Select Active Loan", list(loan_opts.keys()))
        repay_amt = st.number_input("Repayment Amount", min_value=0.01, step=20.0)
        if st.form_submit_button("Apply Repayment", type="primary"):
          l_row = loan_opts[chosen_l]
          new_paid = float(l_row["amount_paid"] or 0.0) + float(repay_amt)
          new_bal = max(0.0, float(l_row["balance_due"] or 0.0) - float(repay_amt))
          exec_sql(
              "UPDATE farm_loans SET amount_paid = ?, balance_due = ? WHERE loan_id = ?",
              (new_paid, new_bal, l_row["loan_id"]),
          )
          st.success(f"Updated repayment for `{l_row['loan_id']}`.")
          st.rerun()
    else:
      st.info("No active unpaid farm loans.")

  st.markdown("---")
  df_all_loans = read_df("SELECT * FROM farm_loans ORDER BY date_taken DESC")
  if not df_all_loans.empty:
    st.dataframe(df_all_loans, use_container_width=True, hide_index=True)
  else:
    st.info("No farm loans recorded yet.")

# ---------------------------------------------------------
# 7. ADMIN USER & PASSWORD CONTROL
# ---------------------------------------------------------
elif nav == "🛡️ Admin User & Password Control":
  if not is_admin:
    st.error("Administrator access required.")
    st.stop()

  st.subheader("🛡️ Admin User Management & Password Reset")
  df_users = read_df("SELECT id, username, full_name, role FROM users ORDER BY id ASC")
  st.dataframe(df_users, use_container_width=True, hide_index=True)

  c_add, c_pwd = st.columns(2)
  with c_add:
    st.markdown("#### Create New User Account")
    with st.form("create_farm_user_form", clear_on_submit=True):
      u_name = st.text_input("Username").strip()
      u_full = st.text_input("Full Name").strip()
      u_role = st.selectbox("Role", ["staff", "admin"])
      u_pass = st.text_input("Initial Password", type="password").strip()
      if st.form_submit_button("Create Account", type="primary"):
        if not u_name or not u_full or not u_pass:
          st.warning("Please complete username, full name, and password.")
        else:
          try:
            exec_sql(
                "INSERT INTO users (username, full_name, role, password) VALUES (?, ?, ?, ?)",
                (u_name, u_full, u_role, u_pass),
            )
            st.success(f"Created {u_role} account `{u_name}`.")
            st.rerun()
          except sqlite3.IntegrityError:
            st.error(f"Username `{u_name}` already exists.")

  with c_pwd:
    st.markdown("#### Reset User Password")
    if not df_users.empty:
      with st.form("reset_farm_user_pwd_form", clear_on_submit=True):
        target_u = st.selectbox("Select User", df_users["username"].tolist())
        new_p = st.text_input("New Password", type="password").strip()
        if st.form_submit_button("Update Password", type="primary"):
          if not new_p:
            st.warning("Enter a new password.")
          else:
            exec_sql("UPDATE users SET password = ? WHERE username = ?", (new_p, target_u))
            st.success(f"Password updated for `{target_u}`.")
            st.rerun()
