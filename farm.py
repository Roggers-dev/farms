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
    page_title="D&P FARMS — Animal Farm Management System",
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
        "https://images.unsplash.com/photo-1516467508483-a7212febe31a?auto=format&fit=crop&w=800&h=520&q=80"
    ),
    "Poultry (Broilers / Layers)": (
        "https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?auto=format&fit=crop&w=800&h=520&q=80"
    ),
    "Cattle": (
        "https://images.unsplash.com/photo-1570042225831-d98fa7577f1e?auto=format&fit=crop&w=800&h=520&q=80"
    ),
    "Goats": (
        "https://images.unsplash.com/photo-1524024973431-2ad916746881?auto=format&fit=crop&w=800&h=520&q=80"
    ),
    "Sheep": (
        "https://images.unsplash.com/photo-1484557985045-edf25e08da73?auto=format&fit=crop&w=800&h=520&q=80"
    ),
    "Rabbits": (
        "https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?auto=format&fit=crop&w=800&h=520&q=80"
    ),
    "Other Livestock": (
        "https://images.unsplash.com/photo-1500595046711-ee27150ad24e?auto=format&fit=crop&w=800&h=520&q=80"
    ),
}

# Species-specific dynamic defaults, labels, feeds, products, diseases & medications
ANIMAL_PROFILES = {
    "Pigs / Swine": {
        "housing_label": "Pigsty / Pen Number",
        "housing_presets": ["Pigsty-01", "Pigsty-02", "Farrowing Pen-01", "Grower Pen-01", "Boar Pen-01"],
        "id_prefix": "PIG",
        "sex_options": ["Sow (Female)", "Boar (Male)", "Gilt (Young Female)", "Piglets Batch", "Mixed Batch"],
        "repro_event_label": "Mating / Crossing Date",
        "birth_event_label": "Farrowing Date (Piglets)",
        "product_categories": [
            "Birth Given (Piglets Litter)",
            "Pork / Live Weight Sold",
            "Weaned Piglets",
            "Manure / Slurry",
            "Other Pig Product",
        ],
        "product_units": ["Piglets", "kg", "Litres", "Bags", "Units"],
        "product_details": ["Farrowing litter born", "Weaned batch", "Grower live weight", "Organic pig manure"],
        "feed_types": ["Creep Feed", "Pig Starter Mash", "Pig Grower Mash", "Pig Finisher Mash", "Lactating Sow Feed"],
        "food_types": ["Maize Bran", "Soybean Meal", "Cassava Peels", "Palm Kernel Cake", "Fish Meal"],
        "food_of_what_presets": ["50kg bags of feed", "25kg bags", "Buckets", "Basins", "Crates"],
        "loss_of_what_presets": ["Newborn piglets", "Weaners", "Grower pigs", "Adult sow", "Boar"],
        "diseases": ["Swine Fever", "Mange / Skin Parasites", "Piglet Scours (Diarrhea)", "Worms / Deworming", "Respiratory Infection"],
        "medications": ["Oxytetracycline", "Ivermectin", "Iron Dextran Injection", "Albendazole Dewormer", "Multivitamin"],
        "inv_items": ["Grower Pigs", "Weaned Piglets", "Pig Starter Bags", "Pork Carcass", "Breeding Sow"],
    },
    "Poultry (Broilers / Layers)": {
        "housing_label": "Coop / Poultry House",
        "housing_presets": ["Broiler House-A", "Layer House-B", "Brooder Room-1", "Battery Cage-1", "Chicks Pen-1"],
        "id_prefix": "PLT",
        "sex_options": ["Layers (Hens)", "Broilers (Mixed)", "Cockerels (Male)", "Day-Old Chicks Batch"],
        "repro_event_label": "Incubation / Hatchery Set Date",
        "birth_event_label": "Hatching Date (Chicks)",
        "product_categories": [
            "Eggs Laid",
            "Total Chicks",
            "Chicks Birth by Animal ID",
            "Dressed Chicken / Broilers",
            "Poultry Litter / Manure",
            "Other Poultry Product",
        ],
        "product_units": ["Crates (30 Eggs)", "Eggs", "Chicks", "Birds", "kg", "Bags"],
        "product_details": ["Morning egg collection", "Afternoon egg collection", "Hatchery batch", "Broiler harvest"],
        "feed_types": ["Chick Starter Crumbs", "Broiler Finisher Pellets", "Grower Mash", "Layer Mash", "Pre-Layer Mash"],
        "food_types": ["Crushed Maize", "Oyster Shell Calcium", "Fish Meal Concentrate", "Soybean Cake", "Vitamin Premix"],
        "food_of_what_presets": ["50kg bags of mash", "25kg bags", "Feeders", "Bags of maize", "Sachets"],
        "loss_of_what_presets": ["Day-old chicks", "Broiler birds", "Layer hens", "Cockerels", "Brooder batch"],
        "diseases": ["Newcastle Disease", "Gumboro (IBD)", "Coccidiosis", "Fowl Pox", "Chronic Respiratory Disease (CRD)"],
        "medications": ["Amprolium", "Lasota Vaccine", "Gumboro Vaccine", "Enrofloxacin", "Vitalyte / Electrolytes"],
        "inv_items": ["Egg Crates (30s)", "Live Broilers", "Spent Layers", "Day-Old Chicks", "Layer Mash Bags"],
    },
    "Cattle": {
        "housing_label": "Kraal / Barn / Paddock",
        "housing_presets": ["Kraal-01", "Dairy Barn-A", "Calf Pen-01", "Paddock-North", "Quarantine Kraal"],
        "id_prefix": "CTL",
        "sex_options": ["Cow (Female)", "Bull (Male)", "Heifer (Young Female)", "Calf", "Mixed Herd"],
        "repro_event_label": "Service / AI Crossing Date",
        "birth_event_label": "Calving Date (Calf Birth)",
        "product_categories": [
            "Milk Volume",
            "Birth Given (Calves)",
            "Beef / Live Cattle",
            "Cow Dung / Manure",
            "Other Cattle Product",
        ],
        "product_units": ["Litres", "Calves", "Head", "kg", "Bags"],
        "product_details": ["Morning milking", "Evening milking", "Healthy calf birth", "Fattened bull sale"],
        "feed_types": ["Dairy Meal", "Beef Fattener Concentrate", "Calf Starter Pellets", "Mineral Lick Block", "Silage"],
        "food_types": ["Napier / Elephant Grass", "Hay Bales", "Brewers Spent Grain", "Cottonseed Cake", "Salt Lick"],
        "food_of_what_presets": ["Hay bales", "50kg concentrate bags", "Wheelbarrows", "Mineral blocks", "Bundles"],
        "loss_of_what_presets": ["Newborn calf", "Weaned calf", "Dairy cow", "Bull", "Heifer"],
        "diseases": ["Foot and Mouth Disease (FMD)", "Mastitis", "Trypanosomiasis", "Tick Fever / Babesiosis", "Lumpy Skin Disease"],
        "medications": ["Oxytetracycline LA", "Diminazene Aceturate", "Intramammary Mastitis Tube", "Ivermectin Pour-On", "Acaricide Spray"],
        "inv_items": ["Fresh Raw Milk (Litres)", "Fattened Bulls", "Dairy Heifers", "Calves", "Hay Bales"],
    },
    "Goats": {
        "housing_label": "Goat Shed / Pen",
        "housing_presets": ["Goat Shed-01", "Kidding Pen-01", "Buck Pen-01", "Doe Pen-02", "Grazing Paddock-1"],
        "id_prefix": "GOT",
        "sex_options": ["Doe (Female)", "Buck (Male)", "Kid (Young)", "Mixed Flock"],
        "repro_event_label": "Breeding / Mating Date",
        "birth_event_label": "Kidding Date (Goat Kids)",
        "product_categories": [
            "Birth Given (Goat Kids)",
            "Milk Volume",
            "Live Goats / Chevon",
            "Goat Manure",
            "Other Goat Product",
        ],
        "product_units": ["Kids", "Litres", "Head", "kg", "Bags"],
        "product_details": ["Twin kids born", "Single kid born", "Goat milk yield", "Market buck"],
        "feed_types": ["Goat Grower Pellets", "Dairy Goat Concentrate", "Kid Starter Feed", "Mineral Block"],
        "food_types": ["Acacia / Leucaena Leaves", "Cassava Peels", "Maize Bran", "Groundnut Haulms", "Salt Lick"],
        "food_of_what_presets": ["50kg bags", "Bundles of browse", "Basins", "Mineral blocks", "Sacks"],
        "loss_of_what_presets": ["Newborn goat kids", "Weaned kids", "Adult doe", "Buck"],
        "diseases": ["PPR (Peste des Petits Ruminants)", "Pneumonia", "Foot Rot", "Internal Worms", "Orf / Sore Mouth"],
        "medications": ["PPR Vaccine", "Albendazole", "Penicillin-Streptomycin", "Oxytetracycline", "Wound Spray"],
        "inv_items": ["Mature Bucks", "Breeding Does", "Weaned Kids", "Goat Milk", "Manure Bags"],
    },
    "Sheep": {
        "housing_label": "Sheep Fold / Pen",
        "housing_presets": ["Sheep Fold-01", "Lambing Pen-01", "Ram Pen-01", "Ewe Pen-02", "Pasture Block-A"],
        "id_prefix": "SHP",
        "sex_options": ["Ewe (Female)", "Ram (Male)", "Lamb (Young)", "Mixed Flock"],
        "repro_event_label": "Tupping / Mating Date",
        "birth_event_label": "Lambing Date (Lambs)",
        "product_categories": [
            "Birth Given (Lambs)",
            "Live Sheep / Mutton",
            "Wool / Fleece",
            "Sheep Manure",
            "Other Sheep Product",
        ],
        "product_units": ["Lambs", "Head", "kg", "Bags"],
        "product_details": ["Lambing birth", "Festive ram batch", "Flock shearing", "Organic manure"],
        "feed_types": ["Sheep Fattener Pellets", "Lamb Creep Feed", "Ewe Lactation Ration", "Mineral Salt Block"],
        "food_types": ["Pasture Hay", "Maize Bran", "Cowpea Husks", "Brewers Grain", "Salt Lick"],
        "food_of_what_presets": ["Hay bales", "50kg bags", "Basins", "Sacks", "Blocks"],
        "loss_of_what_presets": ["Newborn lambs", "Weaned lambs", "Adult ewe", "Ram"],
        "diseases": ["Sheep Pox", "Foot Rot", "Haemonchosis (Barber Pole Worm)", "Pasteurellosis", "Bloat"],
        "medications": ["Ivermectin", "Levamisole Dewormer", "Oxytetracycline", "Foot Rot Zinc Sulfate", "Vitamin B-Complex"],
        "inv_items": ["Fattened Rams", "Breeding Ewes", "Lambs", "Hay Bales"],
    },
    "Rabbits": {
        "housing_label": "Hutch / Cage Row",
        "housing_presets": ["Hutch Row-A", "Kindling Box-01", "Buck Cage-01", "Grower Cage-02", "Rabbitry Unit-1"],
        "id_prefix": "RBT",
        "sex_options": ["Doe (Female)", "Buck (Male)", "Kits / Bunnies", "Mixed Colony"],
        "repro_event_label": "Mating / Service Date",
        "birth_event_label": "Kindling Date (Kits Born)",
        "product_categories": [
            "Birth Given (Kits / Bunnies)",
            "Live Rabbits / Meat",
            "Rabbit Urine (Organic Fertilizer)",
            "Rabbit Pelts / Manure",
            "Other Rabbit Product",
        ],
        "product_units": ["Kits", "Rabbits", "Litres", "kg", "Bags"],
        "product_details": ["Kindling litter born", "Weaned bunnies", "Rabbit urine fertilizer", "Dressed rabbit meat"],
        "feed_types": ["Rabbit Grower Pellets", "Lactating Doe Pellets", "Weaner Pellets"],
        "food_types": ["Tridax / Forage Greens", "Hay", "Sweet Potato Vines", "Carrots / Cabbage Trimmings", "Maize Bran"],
        "food_of_what_presets": ["25kg pellet bags", "50kg bags", "Bundles of greens", "Feed bowls", "Litres"],
        "loss_of_what_presets": ["Newborn kits", "Weaned bunnies", "Breeding doe", "Buck"],
        "diseases": ["Coccidiosis", "Ear Mites (Canker)", "Snuffles (Pasteurella)", "Enteritis / Diarrhea", "Sore Hocks"],
        "medications": ["Sulfaquinoxaline / Amprolium", "Ivermectin Drops", "Enrofloxacin", "Liquid Paraffin (Ear)", "Multivitamin Drops"],
        "inv_items": ["Grower Rabbits", "Breeding Does", "Rabbit Urine (Litres)", "Rabbit Pellets"],
    },
    "Other Livestock": {
        "housing_label": "Enclosure / Pond / Pen",
        "housing_presets": ["Enclosure-01", "Pen-A", "Pond-01", "House-01"],
        "id_prefix": "ANM",
        "sex_options": ["Female", "Male", "Mixed Batch"],
        "repro_event_label": "Crossing / Mating Date",
        "birth_event_label": "Birth / Hatch Date",
        "product_categories": [
            "Birth Given (Offspring / Litter / Kids / Calves)",
            "Milk Volume",
            "Eggs Laid",
            "Total Chicks",
            "Chicks Birth by Animal ID",
            "Other Animal Product",
        ],
        "product_units": ["Units", "kg", "Litres", "Offspring", "Bags"],
        "product_details": ["Daily yield", "Offspring batch", "Harvest batch"],
        "feed_types": ["Standard Concentrate", "Starter Feed", "Grower Feed", "Finisher Feed"],
        "food_types": ["Maize / Grain", "Forage / Greens", "Mineral Supplement"],
        "food_of_what_presets": ["50kg bags", "25kg bags", "Buckets", "Crates"],
        "loss_of_what_presets": ["Young stock", "Adult stock", "Batch"],
        "diseases": ["Parasitic Infection", "Bacterial Infection", "Nutritional Deficiency", "Routine Deworming"],
        "medications": ["Broad-Spectrum Antibiotic", "Dewormer", "Multivitamin"],
        "inv_items": ["Livestock Batch", "Feed Stock", "Farm Produce"],
    },
}

FARM_BG_URL = (
    "https://images.unsplash.com/photo-1500595046711-ee27150ad24e?auto=format&fit=crop&w=1920&q=80"
)

QUANTITY_PRESETS = [1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000]


def get_profile(animal_type):
  return ANIMAL_PROFILES.get(animal_type, ANIMAL_PROFILES["Other Livestock"])


def inject_farm_theme(is_login_screen=False):
  bg_overlay = (
      "linear-gradient(rgba(14, 28, 18, 0.72), rgba(14, 28, 18, 0.78))"
      if is_login_screen
      else "linear-gradient(rgba(244, 248, 243, 0.92), rgba(238, 245, 236, 0.94))"
  )
  st.markdown(
      f"""
      <style>
      .stApp {{
          background-image: {bg_overlay}, url("{FARM_BG_URL}");
          background-size: cover;
          background-position: center;
          background-attachment: fixed;
      }}
      .uniform-animal-card img {{
          width: 100% !important;
          height: 210px !important;
          object-fit: cover !important;
          border-radius: 10px !important;
      }}
      .uniform-hero-img img {{
          width: 100% !important;
          height: 260px !important;
          object-fit: cover !important;
          border-radius: 12px !important;
      }}
      .dp-login-banner {{
          background: rgba(255, 255, 255, 0.96);
          border-left: 8px solid #2e7d32;
          padding: 1.4rem 1.8rem;
          border-radius: 14px;
          box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
          margin-bottom: 1.2rem;
          color: #142818;
      }}
      .dp-login-banner h1 {{
          color: #1b5e20 !important;
          margin: 0 0 0.3rem 0 !important;
          font-size: 2.2rem !important;
          font-weight: 800 !important;
      }}
      .dp-login-banner p {{
          color: #2c3e2e !important;
          margin: 0 !important;
          font-size: 1.02rem !important;
          font-weight: 500 !important;
      }}
      div[data-testid="stForm"] {{
          background: rgba(255, 255, 255, 0.97) !important;
          padding: 1.4rem 1.6rem !important;
          border-radius: 14px !important;
          border: 1px solid #c8e6c9 !important;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.14) !important;
      }}
      div[data-testid="stForm"] label,
      div[data-testid="stForm"] p,
      div[data-testid="stForm"] span,
      div[data-testid="stForm"] h1,
      div[data-testid="stForm"] h2,
      div[data-testid="stForm"] h3,
      div[data-testid="stForm"] h4 {{
          color: #162b1a !important;
          font-weight: 600 !important;
      }}
      div[data-testid="stForm"] input,
      div[data-testid="stForm"] textarea {{
          background-color: #ffffff !important;
          color: #111111 !important;
          border: 1.5px solid #81c784 !important;
          border-radius: 8px !important;
      }}
      div[data-baseweb="tab-list"] {{
          background: rgba(255, 255, 255, 0.95);
          padding: 0.4rem 0.6rem;
          border-radius: 10px;
          gap: 0.5rem;
      }}
      div[data-baseweb="tab-list"] button {{
          color: #1b5e20 !important;
          font-weight: 700 !important;
      }}
      section[data-testid="stSidebar"] {{
          background-color: rgba(24, 48, 30, 0.96) !important;
      }}
      section[data-testid="stSidebar"] * {{
          color: #f1f8e9 !important;
      }}
      </style>
      """,
      unsafe_allow_html=True,
  )


def render_uniform_image(url, caption="", hero=False):
  css_cls = "uniform-hero-img" if hero else "uniform-animal-card"
  st.markdown(f'<div class="{css_cls}">', unsafe_allow_html=True)
  st.image(url, caption=caption, use_container_width=True)
  st.markdown("</div>", unsafe_allow_html=True)


def editable_text_dropdown(
    label,
    options,
    key_prefix,
    placeholder="Or type custom value here...",
    default_blank=False,
    container=None,
):
  """Hybrid dropdown + free-text input: manager can pick a preset OR type any custom value."""
  target = container if container is not None else st
  clean_opts = [str(o) for o in options if str(o).strip()]
  dropdown_list = (
      (["-- Select or Type Custom --"] + clean_opts)
      if default_blank
      else (clean_opts + ["✏️ Type Custom Value"])
  )
  c_sel, c_txt = target.columns([1.15, 1])
  picked = c_sel.selectbox(
      f"{label} (Presets)",
      dropdown_list,
      key=f"{key_prefix}_sel",
  )
  typed = c_txt.text_input(
      f"Or Type {label}",
      placeholder=placeholder,
      key=f"{key_prefix}_txt",
  ).strip()

  if typed:
    return typed
  if picked in ("-- Select or Type Custom --", "✏️ Type Custom Value"):
    return ""
  return picked


def quantity_selector(label, key_prefix, default_preset=10, min_val=0.0, step=1.0):
  col_dd, col_txt = st.columns([1, 1])
  dropdown_choices = [str(x) for x in QUANTITY_PRESETS] + ["✏️ Type Custom Number"]
  default_str = str(default_preset)
  default_idx = (
      dropdown_choices.index(default_str)
      if default_str in dropdown_choices
      else 0
  )
  choice = col_dd.selectbox(
      f"{label} (Quick Select)",
      dropdown_choices,
      index=default_idx,
      key=f"{key_prefix}_dd",
  )
  initial_val = (
      float(choice)
      if choice != "✏️ Type Custom Number"
      else float(default_preset)
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
                VALUES ('admin', 'D&P FARMS Administrator', 'admin', 'admin123')
                ON CONFLICT (username) DO NOTHING
            """)
      )
      conn.execute(
          sqlalchemy.text("""
                INSERT INTO users (username, full_name, role, password)
                VALUES ('staff', 'D&P FARMS Supervisor', 'staff', 'staff123')
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
                VALUES ('admin', 'D&P FARMS Administrator', 'admin', 'admin123')
            """)
      conn.execute("""
                INSERT OR IGNORE INTO users (username, full_name, role, password)
                VALUES ('staff', 'D&P FARMS Supervisor', 'staff', 'staff123')
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
  st.session_state.nav_section = "🏡 Farm Overview & Gallery"


def render_sign_in():
  inject_farm_theme(is_login_screen=True)

  st.markdown(
      """
      <div class="dp-login-banner">
          <h1>🐄 D&amp;P FARMS — Animal Farm Management System</h1>
          <p>Welcome to D&amp;P FARMS. Sign in below to manage livestock, animal products, feed, health, inventory, sales, and farm operations.</p>
      </div>
      """,
      unsafe_allow_html=True,
  )

  preview_cols = st.columns(4)
  for idx, cat in enumerate(["Cattle", "Pigs / Swine", "Poultry (Broilers / Layers)", "Goats"]):
    with preview_cols[idx]:
      render_uniform_image(ANIMAL_IMAGES[cat], caption=cat, hero=False)

  st.markdown("")
  col_left, col_center, col_right = st.columns([1, 2, 1])
  with col_center:
    tab_admin, tab_staff = st.tabs(["🛡️ Admin Sign In", "👤 Staff Sign In"])

    with tab_admin:
      with st.form("admin_sign_in_form"):
        st.subheader("Administrator Sign In")
        adm_user = st.text_input(
            "Admin Username", placeholder="Enter admin username"
        ).strip()
        adm_pass = st.text_input(
            "Admin Password", type="password", placeholder="Enter admin password"
        ).strip()
        if st.form_submit_button("Sign In as Admin", type="primary", use_container_width=True):
          auth = authenticate_user(pg_engine, adm_user, adm_pass)
          if auth and auth["role"] == "admin":
            st.session_state.farm_user = auth
            st.success(f"Welcome to D&P FARMS, {auth['full_name']}!")
            st.rerun()
          elif auth:
            st.error("This account does not have Administrator privileges.")
          else:
            st.error("Invalid admin username or password.")

    with tab_staff:
      with st.form("staff_sign_in_form"):
        st.subheader("Staff / Supervisor Sign In")
        stf_user = st.text_input(
            "Staff Username", placeholder="Enter staff username"
        ).strip()
        stf_pass = st.text_input(
            "Staff Password", type="password", placeholder="Enter staff password"
        ).strip()
        if st.form_submit_button("Sign In as Staff", type="primary", use_container_width=True):
          auth = authenticate_user(pg_engine, stf_user, stf_pass)
          if auth:
            st.session_state.farm_user = auth
            st.success(f"Welcome to D&P FARMS, {auth['full_name']}!")
            st.rerun()
          else:
            st.error("Invalid username or password.")


if st.session_state.farm_user is None:
  render_sign_in()
  st.stop()

inject_farm_theme(is_login_screen=False)

current_user = st.session_state.farm_user
is_admin = current_user["role"] == "admin"

st.markdown(
    f"""
    <div class="dp-login-banner">
        <h1>🐄 D&amp;P FARMS — Management System</h1>
        <p>Signed in as <strong>{current_user['full_name']}</strong> ({current_user['role'].upper()}) — Dynamic Species-Adaptive Entries &amp; Hybrid Presets/Custom Typing.</p>
    </div>
    """,
    unsafe_allow_html=True,
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

st.sidebar.markdown("## 🐄 D&P FARMS")
st.sidebar.markdown(f"**User:** {current_user['full_name']}")
st.sidebar.markdown(f"**Role:** `{current_user['role'].upper()}`")
if use_postgres(pg_engine):
  st.sidebar.success(f"🟢 {db_status_msg}")
else:
  st.sidebar.info(f"🟡 {db_status_msg}")

if st.sidebar.button("🚪 Sign Out"):
  st.session_state.farm_user = None
  st.rerun()

nav_sections = [
    "🏡 Farm Overview & Gallery",
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

nav = st.sidebar.radio("D&P FARMS Pages", nav_sections, key="nav_section")


def get_ids_for_animal_type(a_type):
  if df_animals.empty or "id_number" not in df_animals.columns:
    return []
  sub = df_animals[df_animals["animal_type"] == a_type]
  if sub.empty:
    return df_animals["id_number"].dropna().astype(str).tolist()
  return sub["id_number"].dropna().astype(str).tolist()


def get_rooms_for_animal_type(a_type):
  prof = get_profile(a_type)
  presets = list(prof["housing_presets"])
  if not df_animals.empty and "room_number" in df_animals.columns:
    existing = (
        df_animals[df_animals["animal_type"] == a_type]["room_number"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    for r in existing:
      if r and r != "Unassigned" and r not in presets:
        presets.insert(0, r)
  return presets


# ---------------------------------------------------------
# 0. NEW PAGE: D&P FARMS OVERVIEW & QUICK ENTRY LAUNCHER
# ---------------------------------------------------------
if nav == "🏡 Farm Overview & Gallery":
  st.subheader("🏡 D&P FARMS — Livestock Gallery & Quick Entry Launcher")
  st.caption(
      "Click any animal below to jump straight to that animal's species-adapted "
      "entry form, or review your live farm totals."
  )

  g_cols = st.columns(4)
  for idx, cat in enumerate(ANIMAL_CATEGORIES):
    with g_cols[idx % 4]:
      render_uniform_image(ANIMAL_IMAGES[cat], caption=cat, hero=False)
      count_in_cat = (
          int((df_animals["animal_type"] == cat).sum())
          if not df_animals.empty and "animal_type" in df_animals.columns
          else 0
      )
      st.caption(f"Registered: **{count_in_cat}**")
      if st.button(
          f"➕ Register {cat}",
          key=f"overview_jump_{idx}",
          use_container_width=True,
          type="primary",
      ):
        st.session_state.selected_animal_type = cat
        st.session_state.nav_section = "🐾 Animals & Categories"
        st.rerun()

  st.markdown("---")
  ov1, ov2 = st.columns(2)
  with ov1:
    st.subheader("📊 Livestock Breakdown by Category")
    if not df_animals.empty:
      cat_tbl = (
          df_animals.groupby("animal_type")
          .agg(
              Total_Registered=("id_number", "count"),
              Total_Cost=("cost", "sum"),
          )
          .reset_index()
      )
      st.dataframe(cat_tbl, use_container_width=True, hide_index=True)
    else:
      st.info("No animals registered at D&P FARMS yet.")

  with ov2:
    st.subheader("🥛 Recent Animal Product Output")
    if not df_products.empty:
      st.dataframe(
          df_products[
              [
                  "animal_id",
                  "animal_type",
                  "product_category",
                  "quantity",
                  "unit_label",
                  "record_date",
              ]
          ].head(8),
          use_container_width=True,
          hide_index=True,
      )
    else:
      st.info("No animal product records logged yet.")

# ---------------------------------------------------------
# 1. ANIMALS REGISTERED + UNIFORM PICTURES + DYNAMIC ENTRIES ON SELECTION
# ---------------------------------------------------------
elif nav == "🐾 Animals & Categories":
  st.subheader("🐾 Select an Animal — All Entries Automatically Adapt to That Animal")
  st.caption(
      "Click any animal picture or change the Animal Type selector below. "
      "Housing labels, sex options, breeding/birth dates, and presets update immediately, "
      "and every dropdown lets you pick a preset OR type your own custom value."
  )

  gallery_cols = st.columns(4)
  for idx, cat in enumerate(ANIMAL_CATEGORIES):
    with gallery_cols[idx % 4]:
      render_uniform_image(ANIMAL_IMAGES[cat], caption=cat, hero=False)
      btn_label = (
          f"✅ {cat} (Active)"
          if st.session_state.selected_animal_type == cat
          else f"Select {cat}"
      )
      if st.button(btn_label, key=f"img_jump_{idx}", use_container_width=True):
        st.session_state.selected_animal_type = cat
        st.rerun()

  st.markdown("---")
  # Live selector outside form so changing animal immediately refreshes all dependent fields!
  sel_col1, sel_col2 = st.columns([1, 2])
  with sel_col1:
    chosen_cat = st.selectbox(
        "Active Animal Category",
        ANIMAL_CATEGORIES,
        index=ANIMAL_CATEGORIES.index(st.session_state.selected_animal_type)
        if st.session_state.selected_animal_type in ANIMAL_CATEGORIES
        else 0,
        key="live_animal_cat_selector",
    )
    if chosen_cat != st.session_state.selected_animal_type:
      st.session_state.selected_animal_type = chosen_cat
      st.rerun()

    active_cat = st.session_state.selected_animal_type
    prof = get_profile(active_cat)
    render_uniform_image(
        ANIMAL_IMAGES[active_cat],
        caption=f"Active: {active_cat}",
        hero=True,
    )

  with sel_col2:
    st.markdown(f"### ✍️ Direct Entry Point — {active_cat}")
    st.info(
        f"Fields adapted for **{active_cat}**: `{prof['housing_label']}`, "
        f"`{prof['repro_event_label']}`, and `{prof['birth_event_label']}`. "
        f"Use the preset dropdowns or type any custom text."
    )

    with st.form(f"register_animal_form_{active_cat}", clear_on_submit=True):
      room_number = editable_text_dropdown(
          prof["housing_label"],
          get_rooms_for_animal_type(active_cat),
          key_prefix=f"anim_room_{active_cat}",
          placeholder=f"e.g., {prof['housing_presets'][0]}",
      )
      sex = editable_text_dropdown(
          "Sex / Flock Class",
          prof["sex_options"],
          key_prefix=f"anim_sex_{active_cat}",
          placeholder="Or type custom sex/class...",
      )

      c3, c4 = st.columns(2)
      id_number = c3.text_input(
          f"{active_cat} ID / Tag Number (optional)",
          placeholder=f"e.g., {prof['id_prefix']}-101",
      ).strip()
      cost = c4.number_input("Purchase / Acquisition Cost", min_value=0.0, step=10.0)

      c5, c6, c7, c8 = st.columns(4)
      date_brought = c5.date_input("Date Brought", value=date.today())
      date_of_birth = c6.date_input("Date of Birth / Hatch", value=date.today())
      crossing_date = c7.date_input(prof["repro_event_label"], value=date.today())
      farrow_date = c8.date_input(prof["birth_event_label"], value=date.today())

      c9, c10 = st.columns(2)
      plan_buy_date = c9.date_input("Planning to Buy Time", value=date.today())
      plan_sell_date = c10.date_input("Planning to Sell Time", value=date.today())

      if st.form_submit_button(f"Save {active_cat} Record", type="primary"):
        final_id = (
            id_number
            if id_number
            else f"{prof['id_prefix']}-{uuid.uuid4().hex[:5].upper()}"
        )
        final_room = room_number if room_number else prof["housing_presets"][0]
        final_sex = sex if sex else prof["sex_options"][0]
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
                  active_cat,
                  final_room,
                  str(date_brought),
                  final_sex,
                  float(cost),
                  str(date_of_birth),
                  str(crossing_date),
                  str(farrow_date),
                  str(plan_buy_date),
                  str(plan_sell_date),
              ),
          )
          st.success(
              f"Registered {active_cat} with ID `{final_id}` in `{final_room}`."
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
# 2. ANIMAL PRODUCTS & PERFORMANCE BY ANIMAL ID (DYNAMIC BY ANIMAL)
# ---------------------------------------------------------
elif nav == "🥛 Animal Products & Performance":
  st.subheader("🥛 Animal Products Total & Performance by Animal ID")
  st.caption(
      "Select an Animal Type below—all product categories, units, room presets, "
      "and registered Animal IDs automatically switch to match that animal. "
      "Every dropdown supports both presets and custom typing."
  )

  p_top1, p_top2 = st.columns([1, 2])
  with p_top1:
    prod_animal_type = st.selectbox(
        "Select Animal Type",
        ANIMAL_CATEGORIES,
        index=ANIMAL_CATEGORIES.index(st.session_state.selected_animal_type)
        if st.session_state.selected_animal_type in ANIMAL_CATEGORIES
        else 0,
        key="prod_live_animal_selector",
    )
    st.session_state.selected_animal_type = prod_animal_type
    prof = get_profile(prod_animal_type)
    render_uniform_image(
        ANIMAL_IMAGES[prod_animal_type],
        caption=f"Products for: {prod_animal_type}",
        hero=False,
    )

  with p_top2:
    registered_ids = get_ids_for_animal_type(prod_animal_type)
    with st.form(f"animal_products_form_{prod_animal_type}", clear_on_submit=True):
      final_animal_id = editable_text_dropdown(
          f"{prod_animal_type} ID Number",
          registered_ids,
          key_prefix=f"prod_aid_{prod_animal_type}",
          placeholder=f"Or type ID e.g. {prof['id_prefix']}-01",
          default_blank=True,
      )
      prod_room = editable_text_dropdown(
          prof["housing_label"],
          get_rooms_for_animal_type(prod_animal_type),
          key_prefix=f"prod_room_{prod_animal_type}",
          placeholder=f"e.g., {prof['housing_presets'][0]}",
      )
      prod_category = editable_text_dropdown(
          f"{prod_animal_type} Product / Output Type",
          prof["product_categories"],
          key_prefix=f"prod_cat_{prod_animal_type}",
          placeholder="Or type custom product type...",
      )
      prod_detail = editable_text_dropdown(
          "Product / Birth Details",
          prof["product_details"],
          key_prefix=f"prod_det_{prod_animal_type}",
          placeholder="Or type batch/yield details...",
          default_blank=True,
      )
      unit_label = editable_text_dropdown(
          "Measurement Unit",
          prof["product_units"],
          key_prefix=f"prod_unit_{prod_animal_type}",
          placeholder="e.g., Litres, Crates, Chicks, Kids...",
      )

      prod_qty = quantity_selector(
          "Product Quantity / Volume / Count",
          f"prod_qty_{prod_animal_type}",
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

      if st.form_submit_button(
          f"Save {prod_animal_type} Product Record", type="primary"
      ):
        aid_to_save = (
            final_animal_id
            if final_animal_id
            else f"{prof['id_prefix']}-{uuid.uuid4().hex[:5].upper()}"
        )
        cat_to_save = prod_category or prof["product_categories"][0]
        unit_to_save = unit_label or prof["product_units"][0]

        exec_sql(
            pg_engine,
            """
                  INSERT INTO animal_products (
                      animal_id, animal_type, room_number, product_category,
                      product_detail, quantity, unit_label, record_date, notes
                  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                  """,
            (
                aid_to_save,
                prod_animal_type,
                prod_room or prof["housing_presets"][0],
                cat_to_save,
                prod_detail or cat_to_save,
                float(prod_qty),
                unit_to_save,
                str(prod_date),
                prod_notes,
            ),
        )
        st.success(
            f"Recorded {prod_qty:g} {unit_to_save} ({cat_to_save}) for `{aid_to_save}`."
        )
        st.rerun()

  df_prod_all = read_df(pg_engine, "SELECT * FROM animal_products ORDER BY id DESC")

  st.markdown("---")
  st.subheader("📦 D&P FARMS Product Totals")
  if not df_prod_all.empty:
    milk_tot = float(
        df_prod_all[
            df_prod_all["product_category"].str.contains("Milk", case=False, na=False)
        ]["quantity"]
        .fillna(0)
        .sum()
    )
    eggs_tot = float(
        df_prod_all[
            df_prod_all["product_category"].str.contains("Eggs", case=False, na=False)
        ]["quantity"]
        .fillna(0)
        .sum()
    )
    chicks_tot = float(
        df_prod_all[
            df_prod_all["product_category"].str.contains("Chicks", case=False, na=False)
        ]["quantity"]
        .fillna(0)
        .sum()
    )
    births_tot = float(
        df_prod_all[
            df_prod_all["product_category"].str.contains("Birth", case=False, na=False)
        ]["quantity"]
        .fillna(0)
        .sum()
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Milk Volume", f"{milk_tot:,.2f}")
    m2.metric("Total Eggs Laid", f"{eggs_tot:,.0f}")
    m3.metric("Total Chicks (All / Born)", f"{chicks_tot:,.0f}")
    m4.metric("Total Births / Offspring", f"{births_tot:,.0f}")

    st.markdown("---")
    st.subheader("🏆 Performance by Animal ID (Who Is Doing Well vs. Not)")

    perf_rows = []
    for aid, grp in df_prod_all.groupby("animal_id"):
      a_types = ", ".join(sorted(grp["animal_type"].dropna().unique().tolist()))
      milk_v = float(
          grp[grp["product_category"].str.contains("Milk", case=False, na=False)]["quantity"]
          .fillna(0)
          .sum()
      )
      eggs_v = float(
          grp[grp["product_category"].str.contains("Eggs", case=False, na=False)]["quantity"]
          .fillna(0)
          .sum()
      )
      chicks_v = float(
          grp[grp["product_category"].str.contains("Chicks", case=False, na=False)]["quantity"]
          .fillna(0)
          .sum()
      )
      births_v = float(
          grp[grp["product_category"].str.contains("Birth", case=False, na=False)]["quantity"]
          .fillna(0)
          .sum()
      )
      total_out = float(grp["quantity"].fillna(0).sum())
      other_v = max(0.0, total_out - (milk_v + eggs_v + chicks_v + births_v))
      entries_cnt = len(grp)

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
        "No animal product records yet. Select an animal above and log milk, "
        "eggs, chicks, or birth records."
    )

# ---------------------------------------------------------
# 3. FEED, MORTALITY, DEATH & DAYS (DYNAMIC BY SELECTED ANIMAL)
# ---------------------------------------------------------
elif nav == "🌾 Feed, Mortality, Death & Days":
  st.subheader(
      "🌾 Feed / Food, Separate Mortality & Death, Days Spent & Days Left"
  )
  st.caption(
      "Choose an Animal Type below—housing labels, feed types, food supplements, "
      "'of what?' descriptions, and mortality/death categories automatically adapt. "
      "Every dropdown allows picking a preset OR typing a custom entry."
  )

  f_top1, f_top2 = st.columns([1, 2.2])
  with f_top1:
    a_type = st.selectbox(
        "Select Animal Type",
        ANIMAL_CATEGORIES,
        index=ANIMAL_CATEGORIES.index(st.session_state.selected_animal_type)
        if st.session_state.selected_animal_type in ANIMAL_CATEGORIES
        else 0,
        key="feed_live_animal_selector",
    )
    st.session_state.selected_animal_type = a_type
    prof = get_profile(a_type)
    render_uniform_image(
        ANIMAL_IMAGES[a_type],
        caption=f"Feed & Losses: {a_type}",
        hero=False,
    )

  with f_top2:
    with st.form(f"feed_mortality_form_{a_type}", clear_on_submit=True):
      room_no = editable_text_dropdown(
          prof["housing_label"],
          get_rooms_for_animal_type(a_type),
          key_prefix=f"feed_room_{a_type}",
          placeholder=f"e.g., {prof['housing_presets'][0]}",
      )
      anim_id = editable_text_dropdown(
          f"{a_type} ID / Batch Number",
          get_ids_for_animal_type(a_type),
          key_prefix=f"feed_id_{a_type}",
          placeholder=f"Or type ID e.g. {prof['id_prefix']}-01",
          default_blank=True,
      )
      feed_type = editable_text_dropdown(
          f"{a_type} Feed Type",
          prof["feed_types"],
          key_prefix=f"feed_type_{a_type}",
          placeholder="Or type custom feed...",
      )
      food_type = editable_text_dropdown(
          f"{a_type} Food / Supplement",
          prof["food_types"],
          key_prefix=f"food_type_{a_type}",
          placeholder="Or type custom supplement...",
          default_blank=True,
      )
      food_of_what = editable_text_dropdown(
          "Food Type Quantity — of what?",
          prof["food_of_what_presets"],
          key_prefix=f"food_of_what_{a_type}",
          placeholder="e.g., 50kg bags, hay bales, buckets...",
      )

      other_exp = st.number_input(
          "Other Expenses (optional)", min_value=0.0, step=1.0
      )

      st.markdown("**Quantity & Unit Cost (Quick Select or Type Exact)**")
      qty = quantity_selector(
          "Quantity", f"feed_qty_{a_type}", default_preset=10, min_val=0.0, step=1.0
      )
      unit_cost = quantity_selector(
          "Price / Cost per Unit",
          f"feed_unit_cost_{a_type}",
          default_preset=10,
          min_val=0.0,
          step=1.0,
      )

      st.markdown("---")
      st.markdown(f"**Separate Mortality & Death Tracking ({a_type})**")
      mort_cnt = int(
          quantity_selector(
              "Mortality Count",
              f"mort_cnt_{a_type}",
              default_preset=1,
              min_val=0.0,
              step=1.0,
          )
      )
      mort_of_what = editable_text_dropdown(
          f"Mortality — of what? ({a_type})",
          prof["loss_of_what_presets"],
          key_prefix=f"mort_what_{a_type}",
          placeholder="Or type exact group/animal...",
          default_blank=True,
      )
      mort_date = st.date_input("Date of Mortality", value=date.today())

      death_cnt = int(
          quantity_selector(
              "Death Count",
              f"death_cnt_{a_type}",
              default_preset=1,
              min_val=0.0,
              step=1.0,
          )
      )
      death_of_what = editable_text_dropdown(
          f"Death — of what? ({a_type})",
          prof["loss_of_what_presets"],
          key_prefix=f"death_what_{a_type}",
          placeholder="Or type exact animal/cause...",
          default_blank=True,
      )
      death_date = st.date_input("Date of Death", value=date.today())

      st.markdown("---")
      c9, c10 = st.columns(2)
      date_rec = c9.date_input("Date Recorded / Brought", value=date.today())
      date_fin = c10.date_input("Date Finish (Expected)", value=date.today())

      if st.form_submit_button(
          f"Save {a_type} Feed, Mortality & Death Record", type="primary"
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
                room_no or prof["housing_presets"][0],
                anim_id,
                feed_type or prof["feed_types"][0],
                food_type or feed_type or prof["feed_types"][0],
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
        st.success(f"Saved {a_type} feed, mortality, death, and days record.")
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
# 4. HEALTH, VISIT DATE, DISEASE & MEDICATION (DYNAMIC BY ANIMAL)
# ---------------------------------------------------------
elif nav == "🩺 Health & Medication":
  st.subheader("🩺 Vet Visits, Diseases & Animal Medication")
  st.caption(
      "Select an Animal Type—common diseases, vaccines, medications, housing labels, "
      "and Animal IDs update automatically. Pick from the presets or type custom values."
  )

  h_top1, h_top2 = st.columns([1, 2.2])
  with h_top1:
    h_type = st.selectbox(
        "Select Animal Type",
        ANIMAL_CATEGORIES,
        index=ANIMAL_CATEGORIES.index(st.session_state.selected_animal_type)
        if st.session_state.selected_animal_type in ANIMAL_CATEGORIES
        else 0,
        key="health_live_animal_selector",
    )
    st.session_state.selected_animal_type = h_type
    prof = get_profile(h_type)
    render_uniform_image(
        ANIMAL_IMAGES[h_type],
        caption=f"Health & Vet: {h_type}",
        hero=False,
    )

  with h_top2:
    with st.form(f"health_form_{h_type}", clear_on_submit=True):
      h_id = editable_text_dropdown(
          f"{h_type} ID Number",
          get_ids_for_animal_type(h_type),
          key_prefix=f"health_id_{h_type}",
          placeholder=f"Or type ID e.g. {prof['id_prefix']}-01",
          default_blank=True,
      )
      h_room = editable_text_dropdown(
          prof["housing_label"],
          get_rooms_for_animal_type(h_type),
          key_prefix=f"health_room_{h_type}",
          placeholder=f"e.g., {prof['housing_presets'][0]}",
      )
      disease = editable_text_dropdown(
          f"What {h_type} Disease / Condition?",
          prof["diseases"],
          key_prefix=f"health_dis_{h_type}",
          placeholder="Or type diagnosis/condition...",
      )
      medication = editable_text_dropdown(
          f"{h_type} Medication / Vaccine Given",
          prof["medications"],
          key_prefix=f"health_med_{h_type}",
          placeholder="Or type drug/vaccine name...",
      )

      c_v1, c_v2 = st.columns(2)
      visit_dt = c_v1.date_input("Visit Date", value=date.today())
      vet_cost = c_v2.number_input(
          "Medication / Visit Cost (optional)", min_value=0.0, step=1.0
      )

      if st.form_submit_button(f"Save {h_type} Health Record", type="primary"):
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
                h_room or prof["housing_presets"][0],
                str(visit_dt),
                disease or prof["diseases"][0],
                medication or prof["medications"][0],
                float(vet_cost),
            ),
        )
        st.success(f"Saved health and medication record for {h_type}.")
        st.rerun()

  df_health = read_df(pg_engine, "SELECT * FROM health_logs ORDER BY id DESC")
  if not df_health.empty:
    st.dataframe(df_health, use_container_width=True, hide_index=True)
  else:
    st.info("No health or medication records yet.")

# ---------------------------------------------------------
# 5. INVENTORY, PLANNING TO BUY/SELL, SALES & P/L (DYNAMIC BY ANIMAL)
# ---------------------------------------------------------
elif nav == "📦 Inventory, Planning & Sales/P&L":
  st.subheader("📦 Inventory, Buy/Sell Planning, Sales & Profit/Loss")
  st.caption(
      "Select an Animal Type—item/batch presets and registered IDs adapt to that species. "
      "Choose from the dropdown or type your own description and numbers."
  )

  i_top1, i_top2 = st.columns([1, 2.2])
  with i_top1:
    a_type = st.selectbox(
        "Select Animal Type",
        ANIMAL_CATEGORIES,
        index=ANIMAL_CATEGORIES.index(st.session_state.selected_animal_type)
        if st.session_state.selected_animal_type in ANIMAL_CATEGORIES
        else 0,
        key="inv_live_animal_selector",
    )
    st.session_state.selected_animal_type = a_type
    prof = get_profile(a_type)
    render_uniform_image(
        ANIMAL_IMAGES[a_type],
        caption=f"Inventory & Sales: {a_type}",
        hero=False,
    )

  with i_top2:
    with st.form(f"inv_sales_form_{a_type}", clear_on_submit=True):
      rec_type = st.selectbox("Entry Type", ["Inventory", "Sale"])
      anim_id = editable_text_dropdown(
          f"{a_type} ID / Batch",
          get_ids_for_animal_type(a_type),
          key_prefix=f"inv_id_{a_type}",
          placeholder=f"Or type ID e.g. {prof['id_prefix']}-01",
          default_blank=True,
      )
      item_desc = editable_text_dropdown(
          f"{a_type} Item / Batch Description",
          prof["inv_items"],
          key_prefix=f"inv_item_{a_type}",
          placeholder="Or type custom item/batch...",
      )

      qty = quantity_selector(
          "Quantity", f"inv_qty_{a_type}", default_preset=1, min_val=0.0, step=1.0
      )
      unit_price = quantity_selector(
          "Price per Unit",
          f"inv_price_{a_type}",
          default_preset=10,
          min_val=0.0,
          step=1.0,
      )

      c7, c8, c9 = st.columns(3)
      rec_date = c7.date_input("Transaction Date", value=date.today())
      plan_buy = c8.date_input("Planning to Buy Time", value=date.today())
      plan_sell = c9.date_input("Planning to Sell Time", value=date.today())

      if st.form_submit_button(f"Save {a_type} {rec_type} Entry", type="primary"):
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
                item_desc or prof["inv_items"][0],
                float(qty),
                float(unit_price),
                total_val,
                str(rec_date),
                str(plan_buy),
                str(plan_sell),
            ),
        )
        st.success(f"{a_type} {rec_type} entry saved (Total: {total_val:,.2f}).")
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
      "Pick a preset role/schedule or type your own custom role and amounts."
  )

  col_reg, col_act = st.columns(2)

  with col_reg:
    st.markdown("#### Register New Worker")
    with st.form("add_worker_form", clear_on_submit=True):
      w_name = st.text_input("Worker Full Name (optional)").strip()
      w_role = editable_text_dropdown(
          "Role / Duty",
          [
              "Livestock Attendant",
              "Poultry Caretaker",
              "Pigsty Cleaner & Feeder",
              "Dairy Milker",
              "Farm Supervisor",
              "Security / Night Watch",
          ],
          key_prefix="wrk_role",
          placeholder="Or type custom duty...",
      )
      w_cycle = editable_text_dropdown(
          "Pay Schedule",
          ["Daily", "Weekly", "Bi-Weekly", "Monthly"],
          key_prefix="wrk_cycle",
          placeholder="Or type custom schedule...",
      )
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
                w_cycle or "Monthly",
                float(w_rate),
            ),
        )
        st.success(f"Registered worker `{final_w_name}` ({w_cycle or 'Monthly'}).")
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
      "Select a lender preset or type your own lender name and loan amounts."
  )

  c_new, c_rep = st.columns(2)

  with c_new:
    st.markdown("#### Take a New Farm Loan")
    with st.form("take_loan_form", clear_on_submit=True):
      lender = editable_text_dropdown(
          "Lender / Bank / Institution",
          [
              "Agricultural Development Bank (ADB)",
              "Rural / Community Bank",
              "Microfinance / Susu Cooperative",
              "Feed Supplier Credit",
              "Private Investor / Partner",
          ],
          key_prefix="loan_lender",
          placeholder="Or type lender/bank name...",
      )
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
