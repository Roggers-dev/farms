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

ANIMAL_PROFILES = {
    "Pigs / Swine": {
        "housing_label": "Pigsty / Pen Number",
        "housing_presets": ["Pigsty-01", "Pigsty-02", "Farrowing Pen-01", "Grower Pen-01", "Boar Pen-01"],
        "id_prefix": "PIG",
        "sex_options": ["Adult Female (Sow)", "Adult Male (Boar)", "Young Female (Gilt / Piglet)", "Young Male (Young Boar / Piglet)", "Piglets Batch", "Mixed Batch"],
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
        "sex_options": ["Adult Female (Layer / Hen)", "Adult Male (Cockerel / Rooster)", "Young Female (Pullet / Chick)", "Young Male (Cockerel Chick)", "Broilers (Mixed)", "Day-Old Chicks Batch"],
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
        "sex_options": ["Adult Female (Cow)", "Adult Male (Bull)", "Young Female (Heifer / Calf)", "Young Male (Bull Calf)", "Calf (Unspecified)", "Mixed Herd"],
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
        "sex_options": ["Adult Female (Doe)", "Adult Male (Buck)", "Young Female (Doeling / Kid)", "Young Male (Buckling / Kid)", "Kid (Young)", "Mixed Flock"],
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
        "sex_options": ["Adult Female (Ewe)", "Adult Male (Ram)", "Young Female (Ewe Lamb)", "Young Male (Ram Lamb)", "Lamb (Young)", "Mixed Flock"],
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
        "sex_options": ["Adult Female (Doe)", "Adult Male (Buck)", "Young Female (Junior Doe / Kit)", "Young Male (Junior Buck / Kit)", "Kits / Bunnies", "Mixed Colony"],
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
        "sex_options": ["Adult Female", "Adult Male", "Young Female", "Young Male", "Mixed Batch"],
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


def classify_gender(sex_val):
  """Classifies any species-specific sex/flock label into Male, Female, or Mixed/Other."""
  s = str(sex_val or "").strip().lower()
  if not s:
    return "Unspecified"
  female_keywords = ["female", "sow", "gilt", "pullet", "doeling", "hen", "layer", "cow", "heifer", "doe", "ewe"]
  male_keywords = ["male", "boar", "buckling", "cockerel", "rooster", "bull", "buck", "ram"]
  # Check female before male because 'female' contains 'male'
  for kw in female_keywords:
    if kw in s:
      return "Female"
  for kw in male_keywords:
    if kw in s:
      return "Male"
  return "Mixed / Unspecified"


def classify_age_gender(sex_val, age_stage_val=""):
  """Classifies an animal into Adult Female, Adult Male, Young Female, Young Male, or Mixed/Other."""
  s = str(sex_val or "").strip().lower()
  st_stage = str(age_stage_val or "").strip().lower()
  gender = classify_gender(s)

  young_keywords = [
      "young", "gilt", "pullet", "heifer", "calf", "kid", "doeling",
      "buckling", "lamb", "kit", "bunny", "bunnies", "piglet", "chick", "junior"
  ]
  is_young = (st_stage == "young") or any(yk in s for yk in young_keywords)

  if gender == "Female":
    return "Young Female" if is_young else "Adult Female"
  if gender == "Male":
    return "Young Male" if is_young else "Adult Male"
  return "Mixed / Other"


def inject_farm_theme(is_login_screen=False):
  bg_overlay = (
      "linear-gradient(rgba(10, 26, 15, 0.78), rgba(10, 26, 15, 0.84))"
      if is_login_screen
      else "linear-gradient(rgba(16, 42, 24, 0.72), rgba(12, 32, 18, 0.80))"
  )
  st.markdown(
      f"""
      <style>
      /* Rich Deep Forest Farm Backdrop + Warm Cream & Emerald High-Contrast Surfaces */
      .stApp {{
          background-image: {bg_overlay}, url("{FARM_BG_URL}");
          background-size: cover;
          background-position: center;
          background-attachment: fixed;
          color: #f4f9f4 !important;
      }}
      .main .block-container {{
          background: rgba(247, 250, 245, 0.96) !important;
          border-radius: 16px !important;
          padding: 1.5rem 2rem !important;
          margin-top: 1rem !important;
          margin-bottom: 2rem !important;
          border: 2px solid #2e7d32 !important;
          box-shadow: 0 12px 32px rgba(0, 0, 0, 0.28) !important;
      }}

      /* Top Header Bar */
      header[data-testid="stHeader"] {{
          background: #102a18 !important;
          border-bottom: 2px solid #43a047 !important;
      }}
      header[data-testid="stHeader"] button,
      header[data-testid="stHeader"] svg {{
          color: #ffffff !important;
          fill: #ffffff !important;
      }}

      /* Main Area Text & All Widget Labels (including inside forms, columns, and selectboxes) */
      .main h1, .main h2, .main h3, .main h4,
      .main p, .main span, .main label, .main li,
      div[data-testid="stWidgetLabel"],
      div[data-testid="stWidgetLabel"] *,
      div[data-testid="stMarkdownContainer"],
      div[data-testid="stMarkdownContainer"] p,
      div[data-testid="stMarkdownContainer"] span,
      div[data-testid="stMarkdownContainer"] li,
      div[data-testid="stCaptionContainer"],
      div[data-testid="stCaptionContainer"] p,
      div[data-testid="stHeadingWithActionElements"],
      div[data-testid="stHeadingWithActionElements"] * {{
          color: #112416 !important;
          -webkit-text-fill-color: #112416 !important;
          opacity: 1 !important;
          visibility: visible !important;
      }}

      /* KPI Metric Cards — Crisp Sage-White Card with Rich Forest Border */
      div[data-testid="stMetric"] {{
          background: #e8f3ea !important;
          border: 2px solid #1b5e20 !important;
          border-radius: 12px !important;
          padding: 0.75rem 0.85rem !important;
          box-shadow: 0 4px 12px rgba(10, 28, 15, 0.14) !important;
      }}
      div[data-testid="stMetric"] *,
      div[data-testid="stMetricLabel"] *,
      div[data-testid="stMetricValue"] * {{
          color: #0e2213 !important;
          -webkit-text-fill-color: #0e2213 !important;
          font-weight: 800 !important;
          opacity: 1 !important;
          visibility: visible !important;
      }}

      /* Gallery Animal Count Badges — Soft Mint-Cream Card with Crisp Dark Text */
      .dp-count-badge {{
          background: #e3f1e6 !important;
          color: #0e2213 !important;
          border: 2px solid #2e7d32 !important;
          border-radius: 10px !important;
          padding: 0.55rem 0.7rem !important;
          margin: 0.45rem 0 0.6rem 0 !important;
          font-size: 0.9rem !important;
          line-height: 1.5 !important;
          box-shadow: 0 3px 8px rgba(10, 28, 15, 0.12) !important;
          opacity: 1 !important;
          visibility: visible !important;
      }}
      .dp-count-badge, .dp-count-badge * {{
          color: #0e2213 !important;
          -webkit-text-fill-color: #0e2213 !important;
          opacity: 1 !important;
          visibility: visible !important;
      }}
      .dp-count-badge strong {{
          color: #14532d !important;
          -webkit-text-fill-color: #14532d !important;
          font-weight: 800 !important;
      }}

      /* Uniform Animal Images */
      .uniform-animal-card img {{
          width: 100% !important;
          height: 210px !important;
          object-fit: cover !important;
          border-radius: 10px !important;
          border: 2px solid #2e7d32 !important;
      }}
      .uniform-hero-img img {{
          width: 100% !important;
          height: 260px !important;
          object-fit: cover !important;
          border-radius: 12px !important;
          border: 2px solid #1b5e20 !important;
      }}

      /* Top Banner Card — Deep Forest Green Card with Crisp Ivory/White Text */
      .dp-login-banner {{
          background: linear-gradient(135deg, #13381e 0%, #1d522c 100%) !important;
          border-left: 8px solid #86efac !important;
          border: 2px solid #2e7d32 !important;
          padding: 1.35rem 1.75rem !important;
          border-radius: 14px !important;
          box-shadow: 0 8px 22px rgba(10, 28, 15, 0.22) !important;
          margin-bottom: 1.2rem !important;
      }}
      .dp-login-banner h1 {{
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          margin: 0 0 0.3rem 0 !important;
          font-size: 2.05rem !important;
          font-weight: 800 !important;
      }}
      .dp-login-banner p, .dp-login-banner strong {{
          color: #e8f5e9 !important;
          -webkit-text-fill-color: #e8f5e9 !important;
          margin: 0 !important;
          font-size: 1rem !important;
      }}

      /* Forms & All Input Controls */
      div[data-testid="stForm"] {{
          background: #f1f7f2 !important;
          padding: 1.4rem 1.6rem !important;
          border-radius: 14px !important;
          border: 2px solid #2e7d32 !important;
          box-shadow: 0 6px 20px rgba(10, 28, 15, 0.12) !important;
      }}
      div[data-testid="stForm"] label,
      div[data-testid="stForm"] div[data-testid="stWidgetLabel"],
      div[data-testid="stForm"] div[data-testid="stWidgetLabel"] * {{
          color: #0e2213 !important;
          -webkit-text-fill-color: #0e2213 !important;
          font-weight: 700 !important;
          opacity: 1 !important;
          visibility: visible !important;
      }}
      .stTextInput input, .stNumberInput input, .stTextArea textarea,
      div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
          background-color: #ffffff !important;
          color: #0e2213 !important;
          -webkit-text-fill-color: #0e2213 !important;
          border: 1.5px solid #2e7d32 !important;
          border-radius: 8px !important;
          font-weight: 600 !important;
          opacity: 1 !important;
      }}
      div[data-baseweb="select"] > div {{
          background-color: #ffffff !important;
          color: #0e2213 !important;
          -webkit-text-fill-color: #0e2213 !important;
          border: 1.5px solid #2e7d32 !important;
          border-radius: 8px !important;
          font-weight: 600 !important;
          opacity: 1 !important;
      }}
      div[data-baseweb="select"] span, div[data-baseweb="select"] svg {{
          color: #0e2213 !important;
          -webkit-text-fill-color: #0e2213 !important;
          fill: #1b5e20 !important;
      }}

      /* Date Input Box & Calendar Button */
      div[data-testid="stDateInput"] > div,
      div[data-testid="stDateInput"] div[data-baseweb="input"],
      div[data-testid="stDateInput"] div[data-baseweb="base-input"] {{
          background-color: #ffffff !important;
          background: #ffffff !important;
          color: #0e2213 !important;
          border: 2px solid #1b5e20 !important;
          border-radius: 8px !important;
      }}
      div[data-testid="stDateInput"] input {{
          background-color: #ffffff !important;
          color: #0e2213 !important;
          -webkit-text-fill-color: #0e2213 !important;
          opacity: 1 !important;
          font-weight: 700 !important;
      }}
      div[data-testid="stDateInput"] input::placeholder {{
          color: #2e7d32 !important;
          -webkit-text-fill-color: #2e7d32 !important;
          opacity: 1 !important;
      }}
      div[data-testid="stDateInput"] button {{
          background-color: #1b5e20 !important;
          color: #ffffff !important;
          border-radius: 6px !important;
          margin: 3px !important;
          padding: 0 8px !important;
          opacity: 1 !important;
          visibility: visible !important;
      }}
      div[data-testid="stDateInput"] button svg,
      div[data-testid="stDateInput"] svg {{
          color: #ffffff !important;
          fill: #ffffff !important;
          opacity: 1 !important;
          visibility: visible !important;
      }}
      div[data-baseweb="calendar"],
      div[data-baseweb="popover"] > div {{
          background-color: #ffffff !important;
          color: #0e2213 !important;
          border: 2px solid #1b5e20 !important;
      }}
      div[data-baseweb="calendar"] *,
      div[data-baseweb="popover"] * {{
          color: #0e2213 !important;
          -webkit-text-fill-color: #0e2213 !important;
      }}

      /* Primary & Secondary Action Buttons — Rich Forest Green & Crisp White Text */
      .stButton > button[kind="primary"],
      .stFormSubmitButton > button[kind="primary"] {{
          background: linear-gradient(135deg, #14532d 0%, #1e6b38 100%) !important;
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          border: 1.5px solid #0e3b1f !important;
          border-radius: 8px !important;
          font-weight: 700 !important;
      }}
      .stButton > button[kind="primary"] *,
      .stFormSubmitButton > button[kind="primary"] * {{
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
      }}
      .stButton > button[kind="secondary"],
      .stFormSubmitButton > button[kind="secondary"],
      .stDownloadButton > button {{
          background-color: #dff0e3 !important;
          color: #114223 !important;
          -webkit-text-fill-color: #114223 !important;
          border: 1.5px solid #1e6b38 !important;
          border-radius: 8px !important;
          font-weight: 700 !important;
      }}
      .stButton > button[kind="secondary"] *,
      .stDownloadButton > button * {{
          color: #114223 !important;
          -webkit-text-fill-color: #114223 !important;
      }}

      /* Tabs */
      div[data-baseweb="tab-list"] {{
          background: #dff0e3 !important;
          padding: 0.4rem 0.6rem !important;
          border-radius: 10px !important;
          border: 1.5px solid #2e7d32 !important;
          gap: 0.5rem !important;
      }}
      div[data-baseweb="tab-list"] button,
      div[data-baseweb="tab-list"] button * {{
          color: #0e2213 !important;
          -webkit-text-fill-color: #0e2213 !important;
          font-weight: 700 !important;
      }}

      /* Sidebar Navigation */
      section[data-testid="stSidebar"] {{
          background-image: linear-gradient(rgba(10, 28, 15, 0.86), rgba(8, 22, 12, 0.92)), url("{FARM_BG_URL}") !important;
          background-size: cover !important;
          background-position: center !important;
          border-right: 3px solid #43a047 !important;
          min-width: 285px !important;
      }}
      section[data-testid="stSidebar"] > div {{
          background: transparent !important;
      }}
      section[data-testid="stSidebar"] h1,
      section[data-testid="stSidebar"] h2,
      section[data-testid="stSidebar"] h3,
      section[data-testid="stSidebar"] p,
      section[data-testid="stSidebar"] span,
      section[data-testid="stSidebar"] label,
      section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] * {{
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          opacity: 1 !important;
          visibility: visible !important;
      }}
      section[data-testid="stSidebar"] [data-testid="stRadio"] label {{
          background-color: #f4faf5 !important;
          border: 2px solid #43a047 !important;
          border-radius: 8px !important;
          padding: 0.48rem 0.72rem !important;
          margin-bottom: 0.38rem !important;
          display: flex !important;
          align-items: center !important;
          width: 100% !important;
          box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
          opacity: 1 !important;
          visibility: visible !important;
      }}
      section[data-testid="stSidebar"] [data-testid="stRadio"] label *,
      section[data-testid="stSidebar"] [data-testid="stRadio"] label p,
      section[data-testid="stSidebar"] [data-testid="stRadio"] label span {{
          color: #0e2213 !important;
          -webkit-text-fill-color: #0e2213 !important;
          font-weight: 700 !important;
          font-size: 0.92rem !important;
          opacity: 1 !important;
          visibility: visible !important;
      }}
      section[data-testid="stSidebar"] button {{
          background-color: #1e6b38 !important;
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          border: 1.5px solid #86efac !important;
          border-radius: 8px !important;
          font-weight: 700 !important;
          opacity: 1 !important;
          visibility: visible !important;
      }}
      section[data-testid="stSidebar"] button * {{
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
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


def date_input_with_display(label, key_prefix, default_date=None):
  """Permits date to be empty (None) by default if none is selected."""
  init_dt = default_date if isinstance(default_date, date) else None
  chosen_dt = st.date_input(label, value=init_dt, key=f"{key_prefix}_dt")
  if chosen_dt is not None:
    st.caption(f"Selected Date: **{chosen_dt.strftime('%Y-%m-%d')}**")
    return chosen_dt.strftime("%Y-%m-%d")
  st.caption("Selected Date: **Empty (None)**")
  return ""


def editable_text_dropdown(
    label,
    options,
    key_prefix,
    placeholder="Or type custom value here...",
    default_blank=False,
    container=None,
):
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


def _migrate_animals_composite_pk(engine):
  if use_postgres(engine):
    with engine.begin() as conn:
      # Check if animals table exists and whether (animal_type, id_number) is already PK
      pk_cols = conn.execute(
          sqlalchemy.text("""
              SELECT a.attname
              FROM pg_index i
              JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
              WHERE i.indrelid = 'animals'::regclass AND i.indisprimary
          """)
      ).fetchall()
      pk_names = [r[0] for r in pk_cols]
      if pk_names and set(pk_names) != {"animal_type", "id_number"}:
        conn.execute(
            sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS animals_v2 (
                    id_number TEXT NOT NULL,
                    animal_type TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    date_brought TEXT,
                    sex TEXT NOT NULL,
                    age_stage TEXT DEFAULT 'Adult',
                    cost DOUBLE PRECISION DEFAULT 0.0,
                    date_of_birth TEXT,
                    crossing_date TEXT,
                    farrow_date TEXT,
                    status TEXT DEFAULT 'Active',
                    plan_buy_date TEXT,
                    plan_sell_date TEXT,
                    PRIMARY KEY (animal_type, id_number)
                )
            """)
        )
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO animals_v2 (
                    id_number, animal_type, room_number, date_brought,
                    sex, age_stage, cost, date_of_birth, crossing_date,
                    farrow_date, status, plan_buy_date, plan_sell_date
                )
                SELECT
                    TRIM(id_number), TRIM(animal_type), room_number, date_brought,
                    sex, COALESCE(age_stage, 'Adult'), COALESCE(cost, 0.0),
                    date_of_birth, crossing_date, farrow_date,
                    COALESCE(status, 'Active'), plan_buy_date, plan_sell_date
                FROM animals
                WHERE TRIM(COALESCE(id_number, '')) <> '' AND TRIM(COALESCE(animal_type, '')) <> ''
                ON CONFLICT (animal_type, id_number) DO NOTHING
            """)
        )
        conn.execute(sqlalchemy.text("DROP TABLE animals"))
        conn.execute(sqlalchemy.text("ALTER TABLE animals_v2 RENAME TO animals"))
  else:
    with sqlite3.connect(SQLITE_PATH) as conn:
      tbl_exists = conn.execute(
          "SELECT name FROM sqlite_master WHERE type='table' AND name='animals'"
      ).fetchone()
      if tbl_exists:
        info = conn.execute("PRAGMA table_info(animals)").fetchall()
        pk_cols = [r[1] for r in info if r[5] > 0]
        if pk_cols and set(pk_cols) != {"animal_type", "id_number"}:
          conn.execute("""
              CREATE TABLE IF NOT EXISTS animals_v2 (
                  id_number TEXT NOT NULL,
                  animal_type TEXT NOT NULL,
                  room_number TEXT NOT NULL,
                  date_brought TEXT,
                  sex TEXT NOT NULL,
                  age_stage TEXT DEFAULT 'Adult',
                  cost REAL DEFAULT 0.0,
                  date_of_birth TEXT,
                  crossing_date TEXT,
                  farrow_date TEXT,
                  status TEXT DEFAULT 'Active',
                  plan_buy_date TEXT,
                  plan_sell_date TEXT,
                  PRIMARY KEY (animal_type, id_number)
              )
          """)
          cols_present = {r[1] for r in info}
          age_expr = "COALESCE(age_stage, 'Adult')" if "age_stage" in cols_present else "'Adult'"
          conn.execute(f"""
              INSERT OR IGNORE INTO animals_v2 (
                  id_number, animal_type, room_number, date_brought,
                  sex, age_stage, cost, date_of_birth, crossing_date,
                  farrow_date, status, plan_buy_date, plan_sell_date
              )
              SELECT
                  TRIM(id_number), TRIM(animal_type), room_number, date_brought,
                  sex, {age_expr}, COALESCE(cost, 0.0),
                  date_of_birth, crossing_date, farrow_date,
                  COALESCE(status, 'Active'), plan_buy_date, plan_sell_date
              FROM animals
              WHERE TRIM(COALESCE(id_number, '')) <> '' AND TRIM(COALESCE(animal_type, '')) <> ''
          """)
          conn.execute("DROP TABLE animals")
          conn.execute("ALTER TABLE animals_v2 RENAME TO animals")
          conn.commit()


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
                    id_number TEXT NOT NULL,
                    animal_type TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    date_brought TEXT,
                    sex TEXT NOT NULL,
                    age_stage TEXT DEFAULT 'Adult',
                    cost DOUBLE PRECISION DEFAULT 0.0,
                    date_of_birth TEXT,
                    crossing_date TEXT,
                    farrow_date TEXT,
                    status TEXT DEFAULT 'Active',
                    plan_buy_date TEXT,
                    plan_sell_date TEXT,
                    PRIMARY KEY (animal_type, id_number)
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
                    date_recorded TEXT,
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
      conn.execute(sqlalchemy.text("ALTER TABLE animals ADD COLUMN IF NOT EXISTS age_stage TEXT DEFAULT 'Adult'"))
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
                    visit_date TEXT,
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
                    record_date TEXT,
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
                    offspring_sex TEXT DEFAULT 'Unspecified',
                    quantity DOUBLE PRECISION DEFAULT 0.0,
                    unit_label TEXT,
                    record_date TEXT,
                    notes TEXT
                )
            """)
      )
      conn.execute(
          sqlalchemy.text(
              "ALTER TABLE animal_products ADD COLUMN IF NOT EXISTS offspring_sex TEXT DEFAULT 'Unspecified'"
          )
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
                    entry_date TEXT,
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
                    date_taken TEXT,
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
    _migrate_animals_composite_pk(engine)
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
                    id_number TEXT NOT NULL,
                    animal_type TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    date_brought TEXT,
                    sex TEXT NOT NULL,
                    age_stage TEXT DEFAULT 'Adult',
                    cost REAL DEFAULT 0.0,
                    date_of_birth TEXT,
                    crossing_date TEXT,
                    farrow_date TEXT,
                    status TEXT DEFAULT 'Active',
                    plan_buy_date TEXT,
                    plan_sell_date TEXT,
                    PRIMARY KEY (animal_type, id_number)
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
                    date_recorded TEXT,
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
      anim_cols = {
          row[1]
          for row in conn.execute("PRAGMA table_info(animals)").fetchall()
      }
      if "age_stage" not in anim_cols:
        conn.execute("ALTER TABLE animals ADD COLUMN age_stage TEXT DEFAULT 'Adult'")
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
                    visit_date TEXT,
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
                    record_date TEXT,
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
                    offspring_sex TEXT DEFAULT 'Unspecified',
                    quantity REAL DEFAULT 0.0,
                    unit_label TEXT,
                    record_date TEXT,
                    notes TEXT
                )
            """)
      prod_cols = {
          row[1]
          for row in conn.execute("PRAGMA table_info(animal_products)").fetchall()
      }
      if "offspring_sex" not in prod_cols:
        conn.execute(
            "ALTER TABLE animal_products ADD COLUMN offspring_sex TEXT DEFAULT 'Unspecified'"
        )
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
                    entry_date TEXT,
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
                    date_taken TEXT,
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
    _migrate_animals_composite_pk(engine)


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
  if start_str and str(start_str).strip() not in ("", "None", "nan"):
    try:
      d_start = datetime.strptime(str(start_str)[:10], "%Y-%m-%d").date()
      days_spent = max(0, (today - d_start).days)
    except ValueError:
      days_spent = 0
  if finish_str and str(finish_str).strip() not in ("", "None", "nan"):
    try:
      d_fin = datetime.strptime(str(finish_str)[:10], "%Y-%m-%d").date()
      days_left = (d_fin - today).days
    except ValueError:
      days_left = 0
  return days_spent, days_left


def to_csv_bytes(df):
  if df is None or df.empty:
    return b""
  return df.to_csv(index=False).encode("utf-8")


def clean_str_val(val):
  if val is None or (isinstance(val, float) and pd.isna(val)):
    return ""
  s = str(val).strip()
  return "" if s in ("None", "nan", "NaT") else s


def safe_float(val, default=0.0):
  try:
    if val is None or (isinstance(val, float) and pd.isna(val)) or str(val).strip() == "":
      return default
    return float(val)
  except Exception:
    return default


def safe_int(val, default=0):
  try:
    if val is None or (isinstance(val, float) and pd.isna(val)) or str(val).strip() == "":
      return default
    return int(float(val))
  except Exception:
    return default


def deduplicate_group_animals(df_animals):
  """Ensures each animal is uniquely counted within its own animal_type group."""
  if df_animals is None or df_animals.empty:
    return pd.DataFrame()
  out = df_animals.copy()
  if "animal_type" in out.columns:
    out["animal_type"] = out["animal_type"].astype(str).str.strip()
  if "id_number" in out.columns:
    out["id_number"] = out["id_number"].astype(str).str.strip()
    out = out[out["id_number"] != ""]
    if "animal_type" in out.columns:
      out = out.drop_duplicates(subset=["animal_type", "id_number"], keep="last")
    else:
      out = out.drop_duplicates(subset=["id_number"], keep="last")
  return out


def build_category_gender_summary(df_animals):
  """Returns Adult Female, Adult Male, Young Female, Young Male, Mixed/Other, and Total counts uniquely per animal group."""
  clean_animals = deduplicate_group_animals(df_animals)
  rows = []
  for cat in ANIMAL_CATEGORIES:
    if not clean_animals.empty and "animal_type" in clean_animals.columns:
      sub = clean_animals[clean_animals["animal_type"] == cat]
    else:
      sub = pd.DataFrame()
    total_cnt = len(sub)
    if not sub.empty:
      age_col = sub["age_stage"] if "age_stage" in sub.columns else pd.Series([""] * len(sub), index=sub.index)
      ag_series = [
          classify_age_gender(sx, ag)
          for sx, ag in zip(sub["sex"], age_col)
      ]
      ag_s = pd.Series(ag_series)
      adult_f = int((ag_s == "Adult Female").sum())
      adult_m = int((ag_s == "Adult Male").sum())
      young_f = int((ag_s == "Young Female").sum())
      young_m = int((ag_s == "Young Male").sum())
      other_cnt = int((ag_s == "Mixed / Other").sum())
      cost_sum = float(sub["cost"].fillna(0).sum())
    else:
      adult_f = 0
      adult_m = 0
      young_f = 0
      young_m = 0
      other_cnt = 0
      cost_sum = 0.0
    rows.append({
        "Animal Group": cat,
        "Unique IDs Counted": total_cnt,
        "Adult Females": adult_f,
        "Adult Males": adult_m,
        "Young Females": young_f,
        "Young Males": young_m,
        "Total Females": adult_f + young_f,
        "Total Males": adult_m + young_m,
        "Mixed / Other": other_cnt,
        "Total Animals": total_cnt,
        "Total Cost": cost_sum,
    })
  summary_df = pd.DataFrame(rows)
  totals_row = pd.DataFrame([{
      "Animal Group": "ALL ANIMAL GROUPS TOTAL",
      "Unique IDs Counted": int(summary_df["Unique IDs Counted"].sum()),
      "Adult Females": int(summary_df["Adult Females"].sum()),
      "Adult Males": int(summary_df["Adult Males"].sum()),
      "Young Females": int(summary_df["Young Females"].sum()),
      "Young Males": int(summary_df["Young Males"].sum()),
      "Total Females": int(summary_df["Total Females"].sum()),
      "Total Males": int(summary_df["Total Males"].sum()),
      "Mixed / Other": int(summary_df["Mixed / Other"].sum()),
      "Total Animals": int(summary_df["Total Animals"].sum()),
      "Total Cost": float(summary_df["Total Cost"].sum()),
  }])
  return pd.concat([summary_df, totals_row], ignore_index=True)


pg_engine, db_status_msg = get_pg_engine()
init_db(pg_engine)

NAV_SECTIONS_BASE = [
    "🏡 Farm Overview & Gallery",
    "🐾 Animals & Categories",
    "🥛 Animal Products & Performance",
    "🌾 Feed, Mortality, Death & Days",
    "🩺 Health & Medication",
    "📦 Inventory, Planning & Sales/P&L",
    "👷 Workers: Pay, Credit & Loans",
    "🏦 Farm Loans Taken",
]
NAV_SECTIONS_ADMIN = NAV_SECTIONS_BASE + ["🛡️ Admin User & Password Control"]

if "farm_user" not in st.session_state:
  st.session_state.farm_user = None
if "selected_animal_type" not in st.session_state:
  st.session_state.selected_animal_type = ANIMAL_CATEGORIES[0]
if "active_page" not in st.session_state:
  st.session_state.active_page = NAV_SECTIONS_BASE[0]
if "pending_page_jump" in st.session_state and st.session_state.pending_page_jump:
  st.session_state.active_page = st.session_state.pending_page_jump
  st.session_state.pending_page_jump = None


def request_navigation(target_page):
  st.session_state.pending_page_jump = target_page
  st.rerun()


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
            st.session_state.active_page = NAV_SECTIONS_BASE[0]
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
            st.session_state.active_page = NAV_SECTIONS_BASE[0]
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
allowed_pages = NAV_SECTIONS_ADMIN if is_admin else NAV_SECTIONS_BASE
if st.session_state.active_page not in allowed_pages:
  st.session_state.active_page = allowed_pages[0]

st.markdown(
    f"""
    <div class="dp-login-banner">
        <h1>🐄 D&amp;P FARMS — Management System</h1>
        <p>Signed in as <strong>{current_user['full_name']}</strong> ({current_user['role'].upper()}) — Gender Counts, Editable Records, Optional Dates &amp; CSV Exports.</p>
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

df_animals_unique = deduplicate_group_animals(df_animals)
total_animals = len(df_animals_unique)
if not df_animals_unique.empty:
  _age_all = df_animals_unique["age_stage"] if "age_stage" in df_animals_unique.columns else pd.Series([""] * len(df_animals_unique), index=df_animals_unique.index)
  _ag_all = pd.Series([classify_age_gender(sx, ag) for sx, ag in zip(df_animals_unique["sex"], _age_all)])
  total_adult_females = int((_ag_all == "Adult Female").sum())
  total_adult_males = int((_ag_all == "Adult Male").sum())
  total_young_females = int((_ag_all == "Young Female").sum())
  total_young_males = int((_ag_all == "Young Male").sum())
else:
  total_adult_females = 0
  total_adult_males = 0
  total_young_females = 0
  total_young_males = 0

total_animal_cost = (
    float(df_animals_unique["cost"].fillna(0).sum()) if not df_animals_unique.empty else 0.0
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

k1, k2, k3, k4, k5, k6, k7, k8, k9 = st.columns(9)
k1.metric("Total Animals", total_animals)
k2.metric("Adult Females", total_adult_females)
k3.metric("Adult Males", total_adult_males)
k4.metric("Young Females", total_young_females)
k5.metric("Young Males", total_young_males)
k6.metric("Inventory Value", f"{total_inventory_val:,.2f}")
k7.metric("Total Sales", f"{total_sales:,.2f}")
k8.metric("Total Expenses", f"{total_expenses:,.2f}")
k9.metric(
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

sidebar_choice = st.sidebar.radio(
    "D&P FARMS Pages",
    allowed_pages,
    index=allowed_pages.index(st.session_state.active_page),
    key="dp_sidebar_page_radio",
)
if sidebar_choice != st.session_state.active_page:
  st.session_state.active_page = sidebar_choice
  st.rerun()
nav = st.session_state.active_page


def get_ids_for_animal_type(a_type):
  if (
      df_animals.empty
      or "id_number" not in df_animals.columns
      or "animal_type" not in df_animals.columns
  ):
    return []
  sub = df_animals[df_animals["animal_type"].astype(str).str.strip() == str(a_type).strip()]
  if sub.empty:
    return []
  return (
      sub["id_number"]
      .dropna()
      .astype(str)
      .str.strip()
      .loc[lambda s: s != ""]
      .unique()
      .tolist()
  )


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
# 0. FARM OVERVIEW & QUICK ENTRY LAUNCHER
# ---------------------------------------------------------
if nav == "🏡 Farm Overview & Gallery":
  st.subheader("🏡 D&P FARMS — Livestock Gallery, Gender Counts & Quick Entry Launcher")
  st.caption(
      "Click any animal below to jump straight to that animal's species-adapted "
      "entry form, or review live Female, Male, and Total counts per animal category."
  )
  g_cols = st.columns(4)
  for idx, cat in enumerate(ANIMAL_CATEGORIES):
    with g_cols[idx % 4]:
      render_uniform_image(ANIMAL_IMAGES[cat], caption=cat, hero=False)
      if not df_animals.empty and "animal_type" in df_animals.columns:
        sub_c = df_animals[df_animals["animal_type"] == cat]
        count_in_cat = len(sub_c)
        if not sub_c.empty:
          _ag_c = pd.Series([
              classify_age_gender(sx, ag)
              for sx, ag in zip(
                  sub_c["sex"],
                  sub_c["age_stage"] if "age_stage" in sub_c.columns else [""] * len(sub_c)
              )
          ])
          af_cnt = int((_ag_c == "Adult Female").sum())
          am_cnt = int((_ag_c == "Adult Male").sum())
          yf_cnt = int((_ag_c == "Young Female").sum())
          ym_cnt = int((_ag_c == "Young Male").sum())
        else:
          af_cnt = am_cnt = yf_cnt = ym_cnt = 0
      else:
        count_in_cat = af_cnt = am_cnt = yf_cnt = ym_cnt = 0
      st.markdown(
          f"""
          <div class="dp-count-badge">
              <strong>Total: {count_in_cat}</strong><br/>
              Adult ♀: <strong>{af_cnt}</strong> &nbsp;|&nbsp; Adult ♂: <strong>{am_cnt}</strong><br/>
              Young ♀: <strong>{yf_cnt}</strong> &nbsp;|&nbsp; Young ♂: <strong>{ym_cnt}</strong>
          </div>
          """,
          unsafe_allow_html=True,
      )
      if st.button(
          f"➕ Register {cat}",
          key=f"overview_jump_{idx}",
          use_container_width=True,
          type="primary",
      ):
        st.session_state.selected_animal_type = cat
        request_navigation("🐾 Animals & Categories")

  st.markdown("---")
  st.subheader("📊 Individual Animals Summary: Adult & Young Females and Males")
  gender_summary_df = build_category_gender_summary(df_animals)
  st.dataframe(gender_summary_df, use_container_width=True, hide_index=True)
  st.download_button(
      "⬇️ Download Adult & Young Gender Summary (CSV)",
      data=to_csv_bytes(gender_summary_df),
      file_name="dp_farms_adult_young_gender_summary.csv",
      mime="text/csv",
      key="dl_ov_summary_csv",
  )

  st.markdown("---")
  ov1, ov2 = st.columns([1.15, 1])
  with ov1:
    st.subheader("🐾 Individual Animals Registry Preview")
    if not df_animals.empty:
      df_ov_anim = df_animals.copy()
      _ov_age = df_ov_anim["age_stage"] if "age_stage" in df_ov_anim.columns else [""] * len(df_ov_anim)
      df_ov_anim["age_gender_group"] = [
          classify_age_gender(sx, ag) for sx, ag in zip(df_ov_anim["sex"], _ov_age)
      ]
      ov_cols = [
          c for c in ["id_number", "animal_type", "room_number", "age_stage", "sex", "age_gender_group", "status"]
          if c in df_ov_anim.columns
      ]
      st.dataframe(df_ov_anim[ov_cols].head(10), use_container_width=True, hide_index=True)
    else:
      st.info("No individual animals registered yet.")
  with ov2:
    st.subheader("🥛 Recent Animal Product & Birth Output")
    if not df_products.empty:
      display_cols = [
          c for c in [
              "animal_id",
              "animal_type",
              "product_category",
              "offspring_sex",
              "quantity",
              "unit_label",
              "record_date",
          ]
          if c in df_products.columns
      ]
      st.dataframe(
          df_products[display_cols].head(8),
          use_container_width=True,
          hide_index=True,
      )
    else:
      st.info("No animal product records logged yet.")


# ---------------------------------------------------------
# 1. ANIMALS REGISTERED + GENDER COUNTS + EDITABLE + CSV DOWNLOAD
# ---------------------------------------------------------
elif nav == "🐾 Animals & Categories":
  st.subheader("🐾 Select an Animal — Register, View Gender Counts, Edit & Download CSV")
  st.caption(
      "Click any animal picture or change the Animal Type selector below. "
      "Dates can be left empty if none is selected. Every entry below is editable and downloadable as CSV."
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

    # Individual Category Adult & Young Gender Breakdown Card
    sub_active = (
        df_animals[df_animals["animal_type"] == active_cat]
        if not df_animals.empty
        else pd.DataFrame()
    )
    act_total = len(sub_active)
    if not sub_active.empty:
      _ag_sub = pd.Series([
          classify_age_gender(sx, ag)
          for sx, ag in zip(
              sub_active["sex"],
              sub_active["age_stage"] if "age_stage" in sub_active.columns else [""] * len(sub_active)
          )
      ])
      act_af = int((_ag_sub == "Adult Female").sum())
      act_am = int((_ag_sub == "Adult Male").sum())
      act_yf = int((_ag_sub == "Young Female").sum())
      act_ym = int((_ag_sub == "Young Male").sum())
    else:
      act_af = act_am = act_yf = act_ym = 0
    st.markdown(f"#### 📊 {active_cat} Counts (Total: {act_total})")
    gc1, gc2 = st.columns(2)
    gc1.metric("♀ Adult Females", act_af)
    gc2.metric("♂ Adult Males", act_am)
    gc3, gc4 = st.columns(2)
    gc3.metric("♀ Young Females", act_yf)
    gc4.metric("♂ Young Males", act_ym)

  with sel_col2:
    st.markdown(f"### ✍️ Direct Entry Point — {active_cat}")
    st.info(
        f"Fields adapted for **{active_cat}**: `{prof['housing_label']}`, "
        f"`{prof['repro_event_label']}`, and `{prof['birth_event_label']}`. "
        f"Dates default to empty unless you pick one."
    )
    with st.form(f"register_animal_form_{active_cat}", clear_on_submit=True):
      room_number = editable_text_dropdown(
          prof["housing_label"],
          get_rooms_for_animal_type(active_cat),
          key_prefix=f"anim_room_{active_cat}",
          placeholder=f"e.g., {prof['housing_presets'][0]}",
      )
      age_stage = st.selectbox(
          "Age Group (Adult vs. Young)",
          ["Adult", "Young"],
          key=f"anim_age_stage_{active_cat}",
      )
      sex = editable_text_dropdown(
          "Sex / Gender & Class (Adult/Young Male or Female)",
          prof["sex_options"],
          key_prefix=f"anim_sex_{active_cat}",
          placeholder="Select or type Male / Female...",
      )
      c3, c4 = st.columns(2)
      id_number = c3.text_input(
          f"{active_cat} ID / Tag Number (optional)",
          placeholder=f"e.g., {prof['id_prefix']}-101",
      ).strip()
      cost = c4.number_input("Purchase / Acquisition Cost", min_value=0.0, step=10.0)
      c5, c6, c7, c8 = st.columns(4)
      with c5:
        date_brought = date_input_with_display(
            "Date Brought (Optional)", f"dt_brought_{active_cat}", None
        )
      with c6:
        date_of_birth = date_input_with_display(
            "Date of Birth / Hatch (Optional)", f"dt_dob_{active_cat}", None
        )
      with c7:
        crossing_date = date_input_with_display(
            f"{prof['repro_event_label']} (Optional)", f"dt_cross_{active_cat}", None
        )
      with c8:
        farrow_date = date_input_with_display(
            f"{prof['birth_event_label']} (Optional)", f"dt_farrow_{active_cat}", None
        )
      c9, c10 = st.columns(2)
      with c9:
        plan_buy_date = date_input_with_display(
            "Planning to Buy Time (Optional)", f"dt_pbuy_{active_cat}", None
        )
      with c10:
        plan_sell_date = date_input_with_display(
            "Planning to Sell Time (Optional)", f"dt_psell_{active_cat}", None
        )
      if st.form_submit_button(f"Save {active_cat} Record", type="primary"):
        clean_aid = id_number.strip()
        final_id = (
            clean_aid
            if clean_aid
            else f"{prof['id_prefix']}-{uuid.uuid4().hex[:5].upper()}"
        )
        final_room = room_number if room_number else prof["housing_presets"][0]
        final_sex = sex if sex else prof["sex_options"][0]
        auto_ag_label = classify_age_gender(final_sex, age_stage)
        final_age_stage = "Young" if auto_ag_label.startswith("Young") else age_stage
        existing_in_group = read_df(
            pg_engine,
            "SELECT id_number FROM animals WHERE animal_type = ? AND LOWER(TRIM(id_number)) = LOWER(?)",
            (active_cat, final_id),
        )
        if not existing_in_group.empty:
          st.error(
              f"ID `{final_id}` is already registered in **{active_cat}**. "
              f"Use a unique ID within {active_cat} (the same ID can still be used in other animal groups)."
          )
        else:
          try:
            exec_sql(
                pg_engine,
                """
                INSERT INTO animals (
                    id_number, animal_type, room_number, date_brought,
                    sex, age_stage, cost, date_of_birth, crossing_date, farrow_date,
                    plan_buy_date, plan_sell_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    final_id,
                    active_cat,
                    final_room,
                    date_brought,
                    final_sex,
                    final_age_stage,
                    float(cost),
                    date_of_birth,
                    crossing_date,
                    farrow_date,
                    plan_buy_date,
                    plan_sell_date,
                ),
            )
            st.success(
                f"Registered {active_cat} with unique group ID `{final_id}` ({auto_ag_label} — {final_sex}) in `{final_room}`."
            )
            st.rerun()
          except Exception as exc:
            st.error(f"Could not save animal record: {exc}")

  st.markdown("---")
  st.subheader("📊 Gender & Total Counts by Animal Category")
  df_animals = read_df(pg_engine, "SELECT * FROM animals")
  gender_tbl = build_category_gender_summary(df_animals)
  st.dataframe(gender_tbl, use_container_width=True, hide_index=True)

  if not df_animals.empty:
    df_animals_enriched = df_animals.copy()
    _enr_age = df_animals_enriched["age_stage"] if "age_stage" in df_animals_enriched.columns else [""] * len(df_animals_enriched)
    df_animals_enriched["age_gender_group"] = [
        classify_age_gender(sx, ag) for sx, ag in zip(df_animals_enriched["sex"], _enr_age)
    ]

    st.markdown("---")
    st.subheader(f"🐾 Individual Animal Records ({active_cat}) & CSV Download")
    df_active_records = df_animals_enriched[
        df_animals_enriched["animal_type"] == active_cat
    ].copy()

    dl1, dl2 = st.columns(2)
    with dl1:
      if not df_active_records.empty:
        st.download_button(
            f"⬇️ Download {active_cat} Records (CSV)",
            data=to_csv_bytes(df_active_records),
            file_name=f"dp_farms_{active_cat.lower().replace(' ', '_').replace('/', '_')}_records.csv",
            mime="text/csv",
            key="dl_individual_animal_csv",
        )
    with dl2:
      st.download_button(
          "⬇️ Download ALL Animal Records (CSV)",
          data=to_csv_bytes(df_animals_enriched),
          file_name="dp_farms_all_animal_records.csv",
          mime="text/csv",
          key="dl_all_animals_csv",
      )

    if not df_active_records.empty:
      st.dataframe(df_active_records, use_container_width=True, hide_index=True)
    else:
      st.info(f"No individual records for {active_cat} yet.")

    st.subheader("📋 All Registered Animals Directory (All Categories)")
    st.dataframe(df_animals_enriched, use_container_width=True, hide_index=True)

    st.info(
        "🔒 Editing or deleting registered animal records by Animal ID is restricted to the "
        "**Admin User & Password Control** page."
    )
  else:
    st.info("No animals registered yet.")


# ---------------------------------------------------------
# 2. ANIMAL PRODUCTS & PERFORMANCE (BIRTH MALE/FEMALE + EDITABLE + CSV)
# ---------------------------------------------------------
elif nav == "🥛 Animal Products & Performance":
  st.subheader("🥛 Animal Products Total, Offspring Birth (Male/Female) & Performance")
  st.caption(
      "Select an Animal Type below—product categories, units, room presets, "
      "and registered Animal IDs automatically switch. When recording births, choose Male or Female."
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
          f"{prod_animal_type} Product / Birth / Output Type",
          prof["product_categories"],
          key_prefix=f"prod_cat_{prod_animal_type}",
          placeholder="Or type custom product/birth type...",
      )
      offspring_sex = st.selectbox(
          "Birth / Offspring Gender (Choose Male or Female for Birth Recording)",
          ["Not Applicable (Non-Birth Product)", "Female", "Male", "Mixed (Both Male & Female)"],
          key=f"prod_offspring_sex_{prod_animal_type}",
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
          "Product Quantity / Volume / Birth Count",
          f"prod_qty_{prod_animal_type}",
          default_preset=1,
          min_val=0.0,
          step=1.0,
      )
      c8, c9 = st.columns(2)
      with c8:
        prod_date = date_input_with_display(
            "Date Recorded (Optional)", f"dt_prod_{prod_animal_type}", None
        )
      prod_notes = c9.text_input(
          "Performance / Health Notes (optional)",
          placeholder="e.g., Strong yield / healthy male & female offspring",
      ).strip()
      if st.form_submit_button(
          f"Save {prod_animal_type} Product / Birth Record", type="primary"
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
                product_detail, offspring_sex, quantity, unit_label, record_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                aid_to_save,
                prod_animal_type,
                prod_room or prof["housing_presets"][0],
                cat_to_save,
                prod_detail or cat_to_save,
                offspring_sex,
                float(prod_qty),
                unit_to_save,
                prod_date,
                prod_notes,
            ),
        )
        st.success(
            f"Recorded {prod_qty:g} {unit_to_save} ({cat_to_save} — {offspring_sex}) for `{aid_to_save}`."
        )
        st.rerun()

  df_prod_all = read_df(pg_engine, "SELECT * FROM animal_products ORDER BY id DESC")
  st.markdown("---")
  st.subheader("📦 D&P FARMS Product & Birth Totals")
  if not df_prod_all.empty:
    if "offspring_sex" not in df_prod_all.columns:
      df_prod_all["offspring_sex"] = "Unspecified"

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
    births_mask = df_prod_all["product_category"].str.contains(
        "Birth|Chicks Birth", case=False, na=False
    )
    births_df = df_prod_all[births_mask]
    births_tot = float(births_df["quantity"].fillna(0).sum())
    female_births_tot = float(
        births_df[births_df["offspring_sex"] == "Female"]["quantity"].fillna(0).sum()
    )
    male_births_tot = float(
        births_df[births_df["offspring_sex"] == "Male"]["quantity"].fillna(0).sum()
    )

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Milk Volume", f"{milk_tot:,.2f}")
    m2.metric("Total Eggs Laid", f"{eggs_tot:,.0f}")
    m3.metric("Total Chicks", f"{chicks_tot:,.0f}")
    m4.metric("Total Births", f"{births_tot:,.0f}")
    m5.metric("♀ Female Births", f"{female_births_tot:,.0f}")
    m6.metric("♂ Male Births", f"{male_births_tot:,.0f}")

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
      b_grp = grp[grp["product_category"].str.contains("Birth", case=False, na=False)]
      births_v = float(b_grp["quantity"].fillna(0).sum())
      f_birth_v = float(b_grp[b_grp["offspring_sex"] == "Female"]["quantity"].fillna(0).sum())
      m_birth_v = float(b_grp[b_grp["offspring_sex"] == "Male"]["quantity"].fillna(0).sum())
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
          "Chicks": chicks_v,
          "Female Births": f_birth_v,
          "Male Births": m_birth_v,
          "Total Birth Given": births_v,
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

    st.subheader("🔎 Inspect Individual Animal ID Product Logs & Download CSV")
    selected_inspect_id = st.selectbox(
        "Filter Product Logs by Animal ID",
        ["All Animal IDs"] + df_perf["Animal ID"].tolist(),
        key="inspect_prod_animal_id",
    )
    if selected_inspect_id != "All Animal IDs":
      df_filtered_prod = df_prod_all[df_prod_all["animal_id"] == selected_inspect_id]
      st.dataframe(df_filtered_prod, use_container_width=True, hide_index=True)
      st.download_button(
          f"⬇️ Download {selected_inspect_id} Product Records (CSV)",
          data=to_csv_bytes(df_filtered_prod),
          file_name=f"dp_farms_{selected_inspect_id}_products.csv",
          mime="text/csv",
          key="dl_ind_prod_csv",
      )
    else:
      st.dataframe(df_prod_all, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️ Download ALL Product & Birth Records (CSV)",
        data=to_csv_bytes(df_prod_all),
        file_name="dp_farms_all_product_records.csv",
        mime="text/csv",
        key="dl_all_prod_csv",
    )

    # EDITABLE PRODUCT/BIRTH ENTRIES
    st.markdown("---")
    st.subheader("✏️ Edit Any Product / Birth Record")
    prod_row_ids = df_prod_all["id"].tolist()
    edit_pid = st.selectbox(
        "Select Product / Birth Entry ID to Edit",
        prod_row_ids,
        format_func=lambda x: (
            f"ID #{x} — {df_prod_all[df_prod_all['id']==x].iloc[0]['animal_id']} "
            f"({df_prod_all[df_prod_all['id']==x].iloc[0]['product_category']})"
        ),
        key="select_edit_prod_id",
    )
    p_row = df_prod_all[df_prod_all["id"] == edit_pid].iloc[0]
    with st.form("edit_product_record_form"):
      pe1, pe2, pe3 = st.columns(3)
      ep_aid = pe1.text_input("Animal ID", value=clean_str_val(p_row["animal_id"])).strip()
      ep_atype = pe2.selectbox(
          "Animal Type",
          ANIMAL_CATEGORIES,
          index=ANIMAL_CATEGORIES.index(p_row["animal_type"])
          if p_row["animal_type"] in ANIMAL_CATEGORIES
          else 0,
      )
      ep_room = pe3.text_input("Room / Housing", value=clean_str_val(p_row["room_number"])).strip()

      pe4, pe5, pe6 = st.columns(3)
      ep_cat = pe4.text_input("Product / Birth Category", value=clean_str_val(p_row["product_category"])).strip()
      sex_choices = [
          "Not Applicable (Non-Birth Product)",
          "Female",
          "Male",
          "Mixed (Both Male & Female)",
          "Unspecified",
      ]
      cur_osex = clean_str_val(p_row.get("offspring_sex", "Unspecified")) or "Unspecified"
      if cur_osex not in sex_choices:
        sex_choices.append(cur_osex)
      ep_osex = pe5.selectbox(
          "Birth / Offspring Gender (Male / Female)",
          sex_choices,
          index=sex_choices.index(cur_osex),
      )
      ep_det = pe6.text_input("Product / Birth Detail", value=clean_str_val(p_row["product_detail"])).strip()

      pe7, pe8, pe9, pe10 = st.columns(4)
      ep_qty = pe7.number_input(
          "Quantity / Count", min_value=0.0, value=safe_float(p_row["quantity"], 0.0), step=1.0
      )
      ep_unit = pe8.text_input("Unit Label", value=clean_str_val(p_row["unit_label"])).strip()
      ep_date = pe9.text_input(
          "Record Date (YYYY-MM-DD or empty)", value=clean_str_val(p_row["record_date"])
      ).strip()
      ep_notes = pe10.text_input("Notes", value=clean_str_val(p_row["notes"])).strip()

      pb1, pb2 = st.columns(2)
      if pb1.form_submit_button("💾 Update Product / Birth Record", type="primary"):
        exec_sql(
            pg_engine,
            """
            UPDATE animal_products SET
                animal_id = ?, animal_type = ?, room_number = ?, product_category = ?,
                product_detail = ?, offspring_sex = ?, quantity = ?, unit_label = ?,
                record_date = ?, notes = ?
            WHERE id = ?
            """,
            (
                ep_aid or "General",
                ep_atype,
                ep_room,
                ep_cat,
                ep_det,
                ep_osex,
                float(ep_qty),
                ep_unit,
                ep_date,
                ep_notes,
                int(edit_pid),
            ),
        )
        st.success(f"Updated Product / Birth Record #{edit_pid}.")
        st.rerun()
      if pb2.form_submit_button("🗑️ Delete Product / Birth Record"):
        exec_sql(pg_engine, "DELETE FROM animal_products WHERE id = ?", (int(edit_pid),))
        st.warning(f"Deleted Product / Birth Record #{edit_pid}.")
        st.rerun()
  else:
    st.info(
        "No animal product records yet. Select an animal above and log milk, "
        "eggs, chicks, or birth records."
    )


# ---------------------------------------------------------
# 3. FEED, MORTALITY, DEATH & DAYS (EDITABLE + OPTIONAL DATES + CSV)
# ---------------------------------------------------------
elif nav == "🌾 Feed, Mortality, Death & Days":
  st.subheader(
      "🌾 Feed / Food, Separate Mortality & Death, Days Spent & Days Left"
  )
  st.caption(
      "Choose an Animal Type below. Dates default to empty if none is selected. "
      "All entries can be edited or downloaded as CSV below."
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
              default_preset=0,
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
      mort_date = date_input_with_display(
          "Date of Mortality (Optional)", f"dt_mort_{a_type}", None
      )
      death_cnt = int(
          quantity_selector(
              "Death Count",
              f"death_cnt_{a_type}",
              default_preset=0,
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
      death_date = date_input_with_display(
          "Date of Death (Optional)", f"dt_death_{a_type}", None
      )
      st.markdown("---")
      c9, c10 = st.columns(2)
      with c9:
        date_rec = date_input_with_display(
            "Date Recorded / Brought (Optional)", f"dt_frec_{a_type}", None
        )
      with c10:
        date_fin = date_input_with_display(
            "Date Finish (Expected, Optional)", f"dt_ffin_{a_type}", None
        )
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
                date_rec,
                date_fin,
                int(mort_cnt),
                mort_of_what,
                int(death_cnt),
                death_of_what,
                mort_date,
                death_date,
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

    st.download_button(
        "⬇️ Download Feed, Mortality & Death Records (CSV)",
        data=to_csv_bytes(df_feed),
        file_name="dp_farms_feed_mortality_records.csv",
        mime="text/csv",
        key="dl_feed_csv",
    )

    # EDITABLE FEED & MORTALITY ENTRIES
    st.markdown("---")
    st.subheader("✏️ Edit Any Feed, Mortality & Death Record")
    edit_fid = st.selectbox(
        "Select Feed / Mortality Entry ID to Edit",
        df_feed["id"].tolist(),
        format_func=lambda x: (
            f"ID #{x} — {df_feed[df_feed['id']==x].iloc[0]['animal_type']} | "
            f"{df_feed[df_feed['id']==x].iloc[0]['feed_type']}"
        ),
        key="select_edit_feed_id",
    )
    f_row = df_feed[df_feed["id"] == edit_fid].iloc[0]
    with st.form("edit_feed_record_form"):
      fe1, fe2, fe3 = st.columns(3)
      ef_atype = fe1.selectbox(
          "Animal Type",
          ANIMAL_CATEGORIES,
          index=ANIMAL_CATEGORIES.index(f_row["animal_type"])
          if f_row["animal_type"] in ANIMAL_CATEGORIES
          else 0,
      )
      ef_room = fe2.text_input("Room / Housing", value=clean_str_val(f_row["room_number"])).strip()
      ef_aid = fe3.text_input("Animal ID / Batch", value=clean_str_val(f_row["id_number"])).strip()

      fe4, fe5, fe6 = st.columns(3)
      ef_feed = fe4.text_input("Feed Type", value=clean_str_val(f_row["feed_type"])).strip()
      ef_food = fe5.text_input("Food / Supplement", value=clean_str_val(f_row["food_type"])).strip()
      ef_ofwhat = fe6.text_input(
          "Food Quantity — of what?", value=clean_str_val(f_row["food_quantity_of_what"])
      ).strip()

      fe7, fe8, fe9 = st.columns(3)
      ef_qty = fe7.number_input("Quantity", min_value=0.0, value=safe_float(f_row["quantity"], 0.0), step=1.0)
      ef_ucost = fe8.number_input(
          "Unit Cost", min_value=0.0, value=safe_float(f_row["unit_cost"], 0.0), step=1.0
      )
      ef_oexp = fe9.number_input(
          "Other Expenses", min_value=0.0, value=safe_float(f_row["other_expenses"], 0.0), step=1.0
      )

      fe10, fe11, fe12 = st.columns(3)
      ef_mcnt = fe10.number_input(
          "Mortality Count", min_value=0, value=safe_int(f_row["mortality_count"], 0), step=1
      )
      ef_mwhat = fe11.text_input(
          "Mortality — of what?", value=clean_str_val(f_row["mortality_of_what"])
      ).strip()
      ef_mdate = fe12.text_input(
          "Date of Mortality (YYYY-MM-DD or empty)",
          value=clean_str_val(f_row["date_of_mortality"]),
      ).strip()

      fe13, fe14, fe15 = st.columns(3)
      ef_dcnt = fe13.number_input(
          "Death Count", min_value=0, value=safe_int(f_row["death_count"], 0), step=1
      )
      ef_dwhat = fe14.text_input(
          "Death — of what?", value=clean_str_val(f_row["death_of_what"])
      ).strip()
      ef_ddate = fe15.text_input(
          "Date of Death (YYYY-MM-DD or empty)", value=clean_str_val(f_row["date_of_death"])
      ).strip()

      fe16, fe17 = st.columns(2)
      ef_drec = fe16.text_input(
          "Date Recorded (YYYY-MM-DD or empty)", value=clean_str_val(f_row["date_recorded"])
      ).strip()
      ef_dfin = fe17.text_input(
          "Date Finish (YYYY-MM-DD or empty)", value=clean_str_val(f_row["date_finish"])
      ).strip()

      fb1, fb2 = st.columns(2)
      if fb1.form_submit_button("💾 Update Feed / Mortality Record", type="primary"):
        new_tot = float(ef_qty) * float(ef_ucost)
        exec_sql(
            pg_engine,
            """
            UPDATE feed_and_mortality SET
                animal_type = ?, room_number = ?, id_number = ?, feed_type = ?,
                food_type = ?, food_quantity_of_what = ?, quantity = ?, unit_cost = ?,
                total_cost = ?, date_recorded = ?, date_finish = ?, mortality_count = ?,
                mortality_of_what = ?, death_count = ?, death_of_what = ?,
                date_of_mortality = ?, date_of_death = ?, other_expenses = ?
            WHERE id = ?
            """,
            (
                ef_atype,
                ef_room,
                ef_aid,
                ef_feed,
                ef_food,
                ef_ofwhat,
                float(ef_qty),
                float(ef_ucost),
                new_tot,
                ef_drec,
                ef_dfin,
                int(ef_mcnt),
                ef_mwhat,
                int(ef_dcnt),
                ef_dwhat,
                ef_mdate,
                ef_ddate,
                float(ef_oexp),
                int(edit_fid),
            ),
        )
        st.success(f"Updated Feed / Mortality Record #{edit_fid}.")
        st.rerun()
      if fb2.form_submit_button("🗑️ Delete Feed / Mortality Record"):
        exec_sql(pg_engine, "DELETE FROM feed_and_mortality WHERE id = ?", (int(edit_fid),))
        st.warning(f"Deleted Feed / Mortality Record #{edit_fid}.")
        st.rerun()
  else:
    st.info("No feed, mortality, or death logs yet.")


# ---------------------------------------------------------
# 4. HEALTH, VISIT DATE, DISEASE & MEDICATION (EDITABLE + OPTIONAL DATE + CSV)
# ---------------------------------------------------------
elif nav == "🩺 Health & Medication":
  st.subheader("🩺 Vet Visits, Diseases & Animal Medication")
  st.caption(
      "Select an Animal Type. Visit date defaults to empty if none is selected. "
      "All health logs are editable and downloadable as CSV."
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
      with c_v1:
        visit_dt = date_input_with_display(
            "Visit Date (Optional)", f"dt_visit_{h_type}", None
        )
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
                visit_dt,
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
    st.download_button(
        "⬇️ Download Health & Medication Records (CSV)",
        data=to_csv_bytes(df_health),
        file_name="dp_farms_health_medication_records.csv",
        mime="text/csv",
        key="dl_health_csv",
    )

    # EDITABLE HEALTH RECORDS
    st.markdown("---")
    st.subheader("✏️ Edit Any Health & Medication Record")
    edit_hid = st.selectbox(
        "Select Health Log ID to Edit",
        df_health["id"].tolist(),
        format_func=lambda x: (
            f"ID #{x} — {df_health[df_health['id']==x].iloc[0]['id_number']} | "
            f"{df_health[df_health['id']==x].iloc[0]['disease']}"
        ),
        key="select_edit_health_id",
    )
    h_row = df_health[df_health["id"] == edit_hid].iloc[0]
    with st.form("edit_health_record_form"):
      he1, he2, he3 = st.columns(3)
      eh_aid = he1.text_input("Animal ID", value=clean_str_val(h_row["id_number"])).strip()
      eh_atype = he2.selectbox(
          "Animal Type",
          ANIMAL_CATEGORIES,
          index=ANIMAL_CATEGORIES.index(h_row["animal_type"])
          if h_row["animal_type"] in ANIMAL_CATEGORIES
          else 0,
      )
      eh_room = he3.text_input("Room / Housing", value=clean_str_val(h_row["room_number"])).strip()

      he4, he5, he6, he7 = st.columns(4)
      eh_dis = he4.text_input("Disease / Condition", value=clean_str_val(h_row["disease"])).strip()
      eh_med = he5.text_input("Medication / Vaccine", value=clean_str_val(h_row["medication"])).strip()
      eh_vdate = he6.text_input(
          "Visit Date (YYYY-MM-DD or empty)", value=clean_str_val(h_row["visit_date"])
      ).strip()
      eh_cost = he7.number_input(
          "Vet / Medication Cost", min_value=0.0, value=safe_float(h_row["vet_cost"], 0.0), step=1.0
      )

      hb1, hb2 = st.columns(2)
      if hb1.form_submit_button("💾 Update Health Record", type="primary"):
        exec_sql(
            pg_engine,
            """
            UPDATE health_logs SET
                id_number = ?, animal_type = ?, room_number = ?, visit_date = ?,
                disease = ?, medication = ?, vet_cost = ?
            WHERE id = ?
            """,
            (
                eh_aid or "General",
                eh_atype,
                eh_room,
                eh_vdate,
                eh_dis,
                eh_med,
                float(eh_cost),
                int(edit_hid),
            ),
        )
        st.success(f"Updated Health Record #{edit_hid}.")
        st.rerun()
      if hb2.form_submit_button("🗑️ Delete Health Record"):
        exec_sql(pg_engine, "DELETE FROM health_logs WHERE id = ?", (int(edit_hid),))
        st.warning(f"Deleted Health Record #{edit_hid}.")
        st.rerun()
  else:
    st.info("No health or medication records yet.")


# ---------------------------------------------------------
# 5. INVENTORY, PLANNING TO BUY/SELL, SALES & P/L (EDITABLE + OPTIONAL DATES + CSV)
# ---------------------------------------------------------
elif nav == "📦 Inventory, Planning & Sales/P&L":
  st.subheader("📦 Inventory, Buy/Sell Planning, Sales & Profit/Loss")
  st.caption(
      "Select an Animal Type. Dates default to empty if none is selected. "
      "All inventory and sales entries are editable and downloadable as CSV."
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
      with c7:
        rec_date = date_input_with_display(
            "Transaction Date (Optional)", f"dt_irec_{a_type}", None
        )
      with c8:
        plan_buy = date_input_with_display(
            "Planning to Buy Time (Optional)", f"dt_ibuy_{a_type}", None
        )
      with c9:
        plan_sell = date_input_with_display(
            "Planning to Sell Time (Optional)", f"dt_isell_{a_type}", None
        )
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
                rec_date,
                plan_buy,
                plan_sell,
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
    st.download_button(
        "⬇️ Download Inventory & Sales Records (CSV)",
        data=to_csv_bytes(df_inv_sales),
        file_name="dp_farms_inventory_sales_records.csv",
        mime="text/csv",
        key="dl_inv_sales_csv",
    )

    # EDITABLE INVENTORY & SALES RECORDS
    st.markdown("---")
    st.subheader("✏️ Edit Any Inventory or Sale Record")
    edit_iid = st.selectbox(
        "Select Inventory / Sale ID to Edit",
        df_inv_sales["id"].tolist(),
        format_func=lambda x: (
            f"ID #{x} — [{df_inv_sales[df_inv_sales['id']==x].iloc[0]['record_type']}] "
            f"{df_inv_sales[df_inv_sales['id']==x].iloc[0]['item_or_batch']}"
        ),
        key="select_edit_inv_id",
    )
    i_row = df_inv_sales[df_inv_sales["id"] == edit_iid].iloc[0]
    with st.form("edit_inv_sales_form"):
      ie1, ie2, ie3 = st.columns(3)
      ei_rtype = ie1.selectbox(
          "Entry Type",
          ["Inventory", "Sale"],
          index=0 if i_row["record_type"] == "Inventory" else 1,
      )
      ei_atype = ie2.selectbox(
          "Animal Type",
          ANIMAL_CATEGORIES,
          index=ANIMAL_CATEGORIES.index(i_row["animal_type"])
          if i_row["animal_type"] in ANIMAL_CATEGORIES
          else 0,
      )
      ei_aid = ie3.text_input("Animal ID / Batch", value=clean_str_val(i_row["id_number"])).strip()

      ie4, ie5, ie6 = st.columns(3)
      ei_item = ie4.text_input(
          "Item / Batch Description", value=clean_str_val(i_row["item_or_batch"])
      ).strip()
      ei_qty = ie5.number_input("Quantity", min_value=0.0, value=safe_float(i_row["quantity"], 1.0), step=1.0)
      ei_price = ie6.number_input(
          "Unit Price", min_value=0.0, value=safe_float(i_row["unit_price"], 0.0), step=1.0
      )

      ie7, ie8, ie9 = st.columns(3)
      ei_rdate = ie7.text_input(
          "Transaction Date (YYYY-MM-DD or empty)", value=clean_str_val(i_row["record_date"])
      ).strip()
      ei_pbuy = ie8.text_input(
          "Plan Buy Time (YYYY-MM-DD or empty)", value=clean_str_val(i_row["plan_buy_time"])
      ).strip()
      ei_psell = ie9.text_input(
          "Plan Sell Time (YYYY-MM-DD or empty)", value=clean_str_val(i_row["plan_sell_time"])
      ).strip()

      ib1, ib2 = st.columns(2)
      if ib1.form_submit_button("💾 Update Inventory / Sale Record", type="primary"):
        new_tamt = float(ei_qty) * float(ei_price)
        exec_sql(
            pg_engine,
            """
            UPDATE inventory_and_sales SET
                record_type = ?, animal_type = ?, id_number = ?, item_or_batch = ?,
                quantity = ?, unit_price = ?, total_amount = ?, record_date = ?,
                plan_buy_time = ?, plan_sell_time = ?
            WHERE id = ?
            """,
            (
                ei_rtype,
                ei_atype,
                ei_aid,
                ei_item,
                float(ei_qty),
                float(ei_price),
                new_tamt,
                ei_rdate,
                ei_pbuy,
                ei_psell,
                int(edit_iid),
            ),
        )
        st.success(f"Updated Inventory / Sale Record #{edit_iid}.")
        st.rerun()
      if ib2.form_submit_button("🗑️ Delete Inventory / Sale Record"):
        exec_sql(pg_engine, "DELETE FROM inventory_and_sales WHERE id = ?", (int(edit_iid),))
        st.warning(f"Deleted Inventory / Sale Record #{edit_iid}.")
        st.rerun()
  else:
    st.info("No inventory or sales records yet.")


# ---------------------------------------------------------
# 6. EMPLOY WORKERS: DAILY, WEEKLY, MONTHLY, CREDIT & LOANS (EDITABLE + CSV)
# ---------------------------------------------------------
elif nav == "👷 Workers: Pay, Credit & Loans":
  st.subheader("👷 Workers Registry, Payroll, Credit & Worker Loans")
  st.caption(
      "Pick a preset role/schedule or type your own custom role and amounts. "
      "Date defaults to empty if none is selected. Worker profiles and logs are editable."
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
        act_date = date_input_with_display("Date (Optional)", "dt_wact", None)
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
              (wid, wname, action_type, val, act_date, notes),
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
    st.download_button(
        "⬇️ Download Workers Directory (CSV)",
        data=to_csv_bytes(df_w_display),
        file_name="dp_farms_workers.csv",
        mime="text/csv",
        key="dl_workers_csv",
    )

    st.subheader("✏️ Edit Worker Profile")
    edit_wid = st.selectbox(
        "Select Worker ID to Edit",
        df_w_display["worker_id"].tolist(),
        format_func=lambda x: (
            f"{x} — {df_w_display[df_w_display['worker_id']==x].iloc[0]['full_name']}"
        ),
        key="select_edit_worker_id",
    )
    w_erow = df_w_display[df_w_display["worker_id"] == edit_wid].iloc[0]
    with st.form("edit_worker_profile_form"):
      we1, we2, we3 = st.columns(3)
      ew_name = we1.text_input("Full Name", value=clean_str_val(w_erow["full_name"])).strip()
      ew_role = we2.text_input("Role / Duty", value=clean_str_val(w_erow["role"])).strip()
      ew_cycle = we3.text_input("Pay Schedule", value=clean_str_val(w_erow["pay_cycle"])).strip()

      we4, we5, we6 = st.columns(3)
      ew_rate = we4.number_input("Pay Rate", min_value=0.0, value=safe_float(w_erow["pay_rate"], 0.0), step=5.0)
      ew_cred = we5.number_input(
          "Credit Owed", min_value=0.0, value=safe_float(w_erow["credit_owed"], 0.0), step=5.0
      )
      ew_loan = we6.number_input(
          "Loan Balance", min_value=0.0, value=safe_float(w_erow["loan_balance"], 0.0), step=5.0
      )
      wb1, wb2 = st.columns(2)
      if wb1.form_submit_button("💾 Update Worker Profile", type="primary"):
        exec_sql(
            pg_engine,
            """
            UPDATE workers SET
                full_name = ?, role = ?, pay_cycle = ?, pay_rate = ?,
                credit_owed = ?, loan_balance = ?
            WHERE worker_id = ?
            """,
            (ew_name, ew_role, ew_cycle, float(ew_rate), float(ew_cred), float(ew_loan), edit_wid),
        )
        st.success(f"Updated Worker `{edit_wid}`.")
        st.rerun()
      if wb2.form_submit_button("🗑️ Delete Worker"):
        exec_sql(pg_engine, "DELETE FROM workers WHERE worker_id = ?", (edit_wid,))
        st.warning(f"Deleted Worker `{edit_wid}`.")
        st.rerun()

  df_w_history = read_df(
      pg_engine, "SELECT * FROM worker_finance_logs ORDER BY id DESC"
  )
  if not df_w_history.empty:
    st.subheader("🧾 Worker Pay, Credit & Loan History")
    st.dataframe(df_w_history, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download Worker Finance History (CSV)",
        data=to_csv_bytes(df_w_history),
        file_name="dp_farms_worker_finance_logs.csv",
        mime="text/csv",
        key="dl_wlogs_csv",
    )

    st.subheader("✏️ Edit Worker Finance Log Entry")
    edit_wlid = st.selectbox(
        "Select Finance Log ID to Edit",
        df_w_history["id"].tolist(),
        format_func=lambda x: (
            f"ID #{x} — {df_w_history[df_w_history['id']==x].iloc[0]['worker_name']} | "
            f"{df_w_history[df_w_history['id']==x].iloc[0]['action_type']}"
        ),
        key="select_edit_wlog_id",
    )
    wl_row = df_w_history[df_w_history["id"] == edit_wlid].iloc[0]
    with st.form("edit_worker_log_form"):
      wle1, wle2, wle3, wle4 = st.columns(4)
      ewl_act = wle1.text_input("Action Type", value=clean_str_val(wl_row["action_type"])).strip()
      ewl_amt = wle2.number_input("Amount", min_value=0.0, value=safe_float(wl_row["amount"], 0.0), step=5.0)
      ewl_date = wle3.text_input(
          "Entry Date (YYYY-MM-DD or empty)", value=clean_str_val(wl_row["entry_date"])
      ).strip()
      ewl_notes = wle4.text_input("Notes", value=clean_str_val(wl_row["notes"])).strip()
      wlb1, wlb2 = st.columns(2)
      if wlb1.form_submit_button("💾 Update Finance Log", type="primary"):
        exec_sql(
            pg_engine,
            "UPDATE worker_finance_logs SET action_type = ?, amount = ?, entry_date = ?, notes = ? WHERE id = ?",
            (ewl_act, float(ewl_amt), ewl_date, ewl_notes, int(edit_wlid)),
        )
        st.success(f"Updated Worker Finance Log #{edit_wlid}.")
        st.rerun()
      if wlb2.form_submit_button("🗑️ Delete Finance Log"):
        exec_sql(pg_engine, "DELETE FROM worker_finance_logs WHERE id = ?", (int(edit_wlid),))
        st.warning(f"Deleted Worker Finance Log #{edit_wlid}.")
        st.rerun()


# ---------------------------------------------------------
# 7. FARM LOANS TAKEN BY THE FARM (EDITABLE + OPTIONAL DATE + CSV)
# ---------------------------------------------------------
elif nav == "🏦 Farm Loans Taken":
  st.subheader("🏦 Farm Loans Taken & Repayment Tracking")
  st.caption(
      "Select a lender preset or type your own lender name. Date defaults to empty if none is selected. "
      "All loan entries are editable and downloadable as CSV."
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
      taken_date = date_input_with_display(
          "Date Taken (Optional)", "dt_ltaken", None
      )
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
                taken_date,
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
    st.download_button(
        "⬇️ Download Farm Loans Records (CSV)",
        data=to_csv_bytes(df_all_loans),
        file_name="dp_farms_loans_records.csv",
        mime="text/csv",
        key="dl_loans_csv",
    )

    st.subheader("✏️ Edit Any Farm Loan Record")
    edit_lid = st.selectbox(
        "Select Loan ID to Edit",
        df_all_loans["loan_id"].tolist(),
        format_func=lambda x: (
            f"{x} — {df_all_loans[df_all_loans['loan_id']==x].iloc[0]['lender_name']}"
        ),
        key="select_edit_loan_id",
    )
    l_erow = df_all_loans[df_all_loans["loan_id"] == edit_lid].iloc[0]
    with st.form("edit_farm_loan_form"):
      le1, le2, le3 = st.columns(3)
      el_lender = le1.text_input("Lender Name", value=clean_str_val(l_erow["lender_name"])).strip()
      el_prin = le2.number_input(
          "Principal Amount", min_value=0.0, value=safe_float(l_erow["principal_amount"], 0.0), step=50.0
      )
      el_paid = le3.number_input(
          "Amount Paid", min_value=0.0, value=safe_float(l_erow["amount_paid"], 0.0), step=20.0
      )

      le4, le5, le6 = st.columns(3)
      el_bal = le4.number_input(
          "Balance Due", min_value=0.0, value=safe_float(l_erow["balance_due"], 0.0), step=20.0
      )
      el_dtaken = le5.text_input(
          "Date Taken (YYYY-MM-DD or empty)", value=clean_str_val(l_erow["date_taken"])
      ).strip()
      el_notes = le6.text_input("Notes", value=clean_str_val(l_erow["notes"])).strip()

      lb1, lb2 = st.columns(2)
      if lb1.form_submit_button("💾 Update Farm Loan", type="primary"):
        exec_sql(
            pg_engine,
            """
            UPDATE farm_loans SET
                lender_name = ?, principal_amount = ?, amount_paid = ?,
                balance_due = ?, date_taken = ?, notes = ?
            WHERE loan_id = ?
            """,
            (el_lender, float(el_prin), float(el_paid), float(el_bal), el_dtaken, el_notes, edit_lid),
        )
        st.success(f"Updated Farm Loan `{edit_lid}`.")
        st.rerun()
      if lb2.form_submit_button("🗑️ Delete Farm Loan"):
        exec_sql(pg_engine, "DELETE FROM farm_loans WHERE loan_id = ?", (edit_lid,))
        st.warning(f"Deleted Farm Loan `{edit_lid}`.")
        st.rerun()
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

  st.markdown("---")
  st.subheader("✏️ Admin Only: Edit or Delete Animal Record by Animal Group & Animal ID")
  st.caption(
      "Animal IDs are isolated per animal group. Select the Animal Group first, "
      "then select the Animal ID within that group to edit or delete its record."
  )
  df_adm_animals = read_df(pg_engine, "SELECT * FROM animals ORDER BY animal_type, id_number")
  if not df_adm_animals.empty:
    adm_grp_choice = st.selectbox(
        "1. Select Animal Group",
        ANIMAL_CATEGORIES,
        key="admin_edit_animal_group_sel",
    )
    sub_adm_grp = df_adm_animals[df_adm_animals["animal_type"] == adm_grp_choice]
    grp_id_list = sub_adm_grp["id_number"].dropna().astype(str).tolist()
    if grp_id_list:
      edit_aid_adm = st.selectbox(
          f"2. Select {adm_grp_choice} Animal ID to Edit",
          grp_id_list,
          key="admin_edit_animal_id_sel",
      )
      row_adm_edit = sub_adm_grp[sub_adm_grp["id_number"].astype(str) == str(edit_aid_adm)].iloc[0]
      with st.form("admin_edit_animal_record_form"):
        ec1, ec2, ec3, ec3b = st.columns(4)
        new_atype = ec1.selectbox(
            "Animal Group",
            ANIMAL_CATEGORIES,
            index=ANIMAL_CATEGORIES.index(row_adm_edit["animal_type"])
            if row_adm_edit["animal_type"] in ANIMAL_CATEGORIES
            else 0,
        )
        new_room = ec2.text_input(
            "Housing / Pen / Room", value=clean_str_val(row_adm_edit["room_number"])
        ).strip()
        cur_astage = clean_str_val(row_adm_edit.get("age_stage", "Adult")) or "Adult"
        age_opts = ["Adult", "Young"]
        if cur_astage not in age_opts:
          age_opts.append(cur_astage)
        new_age_stage = ec3.selectbox(
            "Age Group (Adult / Young)", age_opts, index=age_opts.index(cur_astage)
        )
        new_sex = ec3b.text_input(
            "Sex / Gender (Male / Female / Class)", value=clean_str_val(row_adm_edit["sex"])
        ).strip()

        ec4, ec5, ec6 = st.columns(3)
        new_cost = ec4.number_input(
            "Acquisition Cost",
            min_value=0.0,
            value=safe_float(row_adm_edit["cost"], 0.0),
            step=10.0,
        )
        status_opts = ["Active", "Sold", "Deceased", "Transferred", "Quarantine"]
        cur_status = clean_str_val(row_adm_edit.get("status", "Active")) or "Active"
        if cur_status not in status_opts:
          status_opts.append(cur_status)
        new_status = ec5.selectbox(
            "Status", status_opts, index=status_opts.index(cur_status)
        )
        new_dbrought = ec6.text_input(
            "Date Brought (YYYY-MM-DD or empty)",
            value=clean_str_val(row_adm_edit["date_brought"]),
        ).strip()

        ec7, ec8, ec9, ec10, ec11 = st.columns(5)
        new_dob = ec7.text_input(
            "Date of Birth (YYYY-MM-DD or empty)",
            value=clean_str_val(row_adm_edit["date_of_birth"]),
        ).strip()
        new_cross = ec8.text_input(
            "Crossing Date (YYYY-MM-DD or empty)",
            value=clean_str_val(row_adm_edit["crossing_date"]),
        ).strip()
        new_farrow = ec9.text_input(
            "Birth/Farrow Date (YYYY-MM-DD or empty)",
            value=clean_str_val(row_adm_edit["farrow_date"]),
        ).strip()
        new_pbuy = ec10.text_input(
            "Plan Buy Date (YYYY-MM-DD or empty)",
            value=clean_str_val(row_adm_edit["plan_buy_date"]),
        ).strip()
        new_psell = ec11.text_input(
            "Plan Sell Date (YYYY-MM-DD or empty)",
            value=clean_str_val(row_adm_edit["plan_sell_date"]),
        ).strip()

        b_upd, b_del = st.columns(2)
        save_edit_btn = b_upd.form_submit_button("💾 Update Animal Record", type="primary")
        del_edit_btn = b_del.form_submit_button("🗑️ Delete This Animal Record")

        if save_edit_btn:
          exec_sql(
              pg_engine,
              """
              UPDATE animals SET
                  animal_type = ?, room_number = ?, date_brought = ?, sex = ?,
                  age_stage = ?, cost = ?, date_of_birth = ?, crossing_date = ?, farrow_date = ?,
                  status = ?, plan_buy_date = ?, plan_sell_date = ?
              WHERE animal_type = ? AND id_number = ?
              """,
              (
                  new_atype,
                  new_room or "Unassigned",
                  new_dbrought,
                  new_sex or "Unspecified",
                  new_age_stage,
                  float(new_cost),
                  new_dob,
                  new_cross,
                  new_farrow,
                  new_status,
                  new_pbuy,
                  new_psell,
                  adm_grp_choice,
                  str(edit_aid_adm),
              ),
          )
          st.success(f"Updated record for {adm_grp_choice} — Animal ID `{edit_aid_adm}`.")
          st.rerun()
        if del_edit_btn:
          exec_sql(
              pg_engine,
              "DELETE FROM animals WHERE animal_type = ? AND id_number = ?",
              (adm_grp_choice, str(edit_aid_adm)),
          )
          st.warning(f"Deleted {adm_grp_choice} — Animal ID `{edit_aid_adm}`.")
          st.rerun()
    else:
      st.info(f"No animals registered under {adm_grp_choice} yet.")
  else:
    st.info("No animals registered in the system yet.")
