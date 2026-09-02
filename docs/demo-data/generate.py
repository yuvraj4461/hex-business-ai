"""Generate a coherent demo dataset for testing HEX's file-upload integration.

    python docs/demo-data/generate.py

Writes 8 CSVs into docs/demo-data/ — one per entity HEX can ingest
(supplier, product, purchase_order, purchase_order_line, shipment,
inventory, transaction, expense). Fictional company: "Aurora Foods", a
packaged-snacks maker in India importing ingredients and packaging.

Links are by name (HEX resolves supplier / product FKs by name match),
so upload all 8 in one connection and hit Sync.
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(11)
HERE = os.path.dirname(os.path.abspath(__file__))


def write(name: str, rows: list[dict]) -> None:
    path = os.path.join(HERE, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  {name:28} {len(rows):>3} rows")


# --------------------------------------------------------------------------
# suppliers
# --------------------------------------------------------------------------
SUPPLIERS = [
    ("Shanghai Ingredients Co", "Ingredients", "ACTIVE", "China", "Shanghai", 28),
    ("Mekong Rice Mills", "Grains", "ACTIVE", "Vietnam", "Ho Chi Minh City", 21),
    ("Gujarat Spice Traders", "Spices", "ACTIVE", "India", "Ahmedabad", 7),
    ("Rotterdam Packaging BV", "Packaging", "ACTIVE", "Netherlands", "Rotterdam", 18),
    ("Kerala Coconut Board", "Ingredients", "ACTIVE", "India", "Kochi", 10),
    ("Sichuan Chili Exports", "Spices", "AT_RISK", "China", "Chengdu", 25),
]
write("supplier.csv", [
    {
        "name": n, "category": c, "status": s, "country": co, "city": ci,
        "lead_time_days": lt,
        "contact_email": f"sales@{n.split()[0].lower()}.example",
    }
    for n, c, s, co, ci, lt in SUPPLIERS
])

# --------------------------------------------------------------------------
# products
# --------------------------------------------------------------------------
PRODUCTS = [
    ("Masala Crunch 100g", "Snacks", 45),
    ("Masala Crunch 200g", "Snacks", 80),
    ("Coconut Bites 90g", "Snacks", 55),
    ("Coconut Bites 180g", "Snacks", 100),
    ("Spicy Rice Puffs 80g", "Snacks", 40),
    ("Spicy Rice Puffs 160g", "Snacks", 72),
    ("Herbal Trail Mix 120g", "Premium", 150),
    ("Herbal Trail Mix 250g", "Premium", 290),
]
write("product.csv", [
    {"name": n, "category": c, "unit_price": p} for n, c, p in PRODUCTS
])

# --------------------------------------------------------------------------
# purchase orders + lines
# --------------------------------------------------------------------------
POS = [
    ("PO-2026-0101", "Shanghai Ingredients Co", "OPEN", "USD", 1_850_000, "FOB",
     "2026-08-05", "2026-09-10"),
    ("PO-2026-0102", "Mekong Rice Mills", "OPEN", "USD", 940_000, "CIF",
     "2026-08-12", "2026-09-08"),
    ("PO-2026-0103", "Gujarat Spice Traders", "RECEIVED", "INR", 320_000, "EXW",
     "2026-07-20", "2026-07-28"),
    ("PO-2026-0104", "Rotterdam Packaging BV", "OPEN", "EUR", 610_000, "FOB",
     "2026-08-18", "2026-09-20"),
    ("PO-2026-0105", "Kerala Coconut Board", "OPEN", "INR", 275_000, "EXW",
     "2026-08-22", "2026-09-05"),
]
write("purchase_order.csv", [
    {"po_number": p, "supplier": s, "status": st, "currency": cur,
     "total_amount": amt, "incoterm": inc, "order_date": od, "expected_date": ed}
    for p, s, st, cur, amt, inc, od, ed in POS
])

PO_LINES = [
    ("PO-2026-0101", "Masala Crunch 200g", "Masala seasoning blend", 5000, 180),
    ("PO-2026-0101", "Spicy Rice Puffs 160g", "Puffed rice base", 8000, 95),
    ("PO-2026-0102", "Spicy Rice Puffs 80g", "Jasmine broken rice", 12000, 42),
    ("PO-2026-0103", "Masala Crunch 100g", "Garam masala", 3000, 60),
    ("PO-2026-0104", "Coconut Bites 180g", "Laminated pouch film", 20000, 12),
    ("PO-2026-0105", "Coconut Bites 90g", "Desiccated coconut", 4000, 55),
]
write("purchase_order_line.csv", [
    {"po_number": p, "product": pr, "description": d, "quantity": q,
     "unit_cost": uc}
    for p, pr, d, q, uc in PO_LINES
])

# --------------------------------------------------------------------------
# shipments — on real corridors so Risk Center / World Watch light up
# --------------------------------------------------------------------------
SHIPMENTS = [
    ("SHP-CN-2001", "PO-2026-0101", "Shanghai Ingredients Co", "Masala Crunch 200g",
     "China", "Shanghai", "India", "Mundra", "Maersk", "SEA", "IN_TRANSIT",
     "2026-08-20", "2026-09-18", 1_850_000, "USD"),
    ("SHP-VN-2002", "PO-2026-0102", "Mekong Rice Mills", "Spicy Rice Puffs 80g",
     "Vietnam", "Ho Chi Minh City", "India", "Nhava Sheva", "CMA CGM", "SEA",
     "IN_TRANSIT", "2026-08-25", "2026-09-14", 940_000, "USD"),
    ("SHP-NL-2003", "PO-2026-0104", "Rotterdam Packaging BV", "Coconut Bites 180g",
     "Netherlands", "Rotterdam", "India", "Mundra", "Hapag-Lloyd", "SEA",
     "PLANNED", "2026-09-01", "2026-09-30", 610_000, "EUR"),
    ("SHP-IN-2004", "PO-2026-0103", "Gujarat Spice Traders", "Masala Crunch 100g",
     "India", "Ahmedabad", "India", "Mumbai", "BlueDart", "ROAD", "ARRIVED",
     "2026-07-22", "2026-07-25", 320_000, "INR"),
]
write("shipment.csv", [
    {
        "reference": r, "po_number": po, "supplier": s, "product": pr,
        "origin_country": oc, "origin_port": op,
        "destination_country": dc, "destination_port": dp,
        "carrier": car, "transport_mode": tm, "status": st,
        "etd": etd, "eta": eta, "value_amount": val, "currency": cur,
    }
    for r, po, s, pr, oc, op, dc, dp, car, tm, st, etd, eta, val, cur in SHIPMENTS
])

# --------------------------------------------------------------------------
# inventory — a few SKUs deliberately below reorder level
# --------------------------------------------------------------------------
INVENTORY = [
    ("Masala Crunch 100g", 4200, 1500, 600),
    ("Masala Crunch 200g", 1800, 1200, 500),
    ("Coconut Bites 90g", 900, 1000, 400),        # low
    ("Coconut Bites 180g", 2600, 900, 350),
    ("Spicy Rice Puffs 80g", 5100, 2000, 800),
    ("Spicy Rice Puffs 160g", 1400, 1000, 400),
    ("Herbal Trail Mix 120g", 320, 500, 200),     # low
    ("Herbal Trail Mix 250g", 150, 300, 120),     # low
]
write("inventory.csv", [
    {"product": p, "quantity": q, "reorder_level": rl, "safety_stock": ss}
    for p, q, rl, ss in INVENTORY
])

# --------------------------------------------------------------------------
# transactions (revenue) — 15 months, with a clear dip
# --------------------------------------------------------------------------
start = date(2025, 6, 1)
base = 1_150_000
tx = []
for i in range(15):
    m = date(start.year + (start.month - 1 + i) // 12,
             (start.month - 1 + i) % 12 + 1, 1)
    trend = base * (1 + 0.02 * i)
    if i in (9, 10):           # a two-month contraction
        trend *= 0.55
    seasonal = 1.25 if m.month in (10, 11) else (0.9 if m.month in (2, 6) else 1.0)
    total = trend * seasonal
    # split into 2-3 payouts per month
    n = random.choice([2, 3])
    for k in range(n):
        amt = round(total / n * random.uniform(0.85, 1.15), 2)
        d = m + timedelta(days=random.randint(3, 25))
        tx.append({
            "transaction_type": "REVENUE",
            "amount": amt,
            "description": f"{d.strftime('%b')} retail & distributor payout",
            "date": d.isoformat(),
        })
write("transaction.csv", tx)

# --------------------------------------------------------------------------
# expenses — 15 months, categories incl. Marketing (for CAC) + fixed overhead
# --------------------------------------------------------------------------
EXP = {
    "Ingredients": (480_000, 0.20),
    "Freight": (150_000, 0.30),
    "Marketing": (90_000, 0.35),
    "Salaries": (410_000, 0.03),
    "Rent": (110_000, 0.0),
    "Utilities": (36_000, 0.10),
    "Packaging": (120_000, 0.25),
}
ex = []
for i in range(15):
    m = date(start.year + (start.month - 1 + i) // 12,
             (start.month - 1 + i) % 12 + 1, 1)
    for cat, (amt, vol) in EXP.items():
        val = round(amt * (1 + 0.015 * i) * random.uniform(1 - vol, 1 + vol), 2)
        d = m + timedelta(days=random.randint(1, 10))
        ex.append({
            "category": cat,
            "amount": val,
            "description": f"{cat} - {d.strftime('%b %Y')}",
            "date": d.isoformat(),
        })
write("expense.csv", ex)

print("\nDone. Upload these in HEX -> Integrations -> New connection -> File upload.")
