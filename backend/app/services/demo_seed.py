"""Seed a compact starter dataset for a freshly-registered organization.

Self-serve signup (`POST /auth/register` with ``seed_demo=true``) calls
``seed_organization`` so the new user lands on a dashboard that already has
suppliers, products, orders, finances, supply routes and a couple of open
purchase orders — instead of an empty shell. Kept deliberately small so
signup stays fast, and industry-agnostic so any industry string works.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import (
    Customer,
    Expense,
    Inventory,
    Order,
    OrderItem,
    Product,
    PurchaseOrder,
    PurchaseOrderLine,
    Supplier,
    SupplyRoute,
    Transaction,
)

logger = logging.getLogger(__name__)

_SUPPLIERS = [
    ("Shenzhen Components Co", "China", "Shenzhen", 24),
    ("Yangtze Materials Ltd", "China", "Shanghai", 21),
    ("Mekong Manufacturing", "Vietnam", "Ho Chi Minh City", 26),
    ("Rhein Industrieteile GmbH", "Germany", "Hamburg", 32),
    ("Bharat Fabricators", "India", "Pune", 6),
    ("Gulf Polymers FZE", "United Arab Emirates", "Jebel Ali", 12),
    ("Pacific Rim Supply", "United States", "Long Beach", 30),
    ("Anadolu Tekstil", "Turkey", "Izmir", 18),
]

# origin_port, origin_country, dest_port, dest_country, mode, corridor,
# distance_km, transit_days, freight_cost
_ROUTES = [
    ("Shanghai", "China", "Mundra", "India", "SEA", "RED_SEA", 7100, 19, 250000),
    ("Shenzhen", "China", "Nhava Sheva", "India", "SEA", "RED_SEA", 7300, 20, 262000),
    ("Ho Chi Minh City", "Vietnam", "Chennai", "India", "SEA", "MALACCA", 4200, 12, 180000),
    ("Hamburg", "Germany", "Mundra", "India", "SEA", "SUEZ", 11200, 24, 410000),
    ("Jebel Ali", "United Arab Emirates", "Nhava Sheva", "India", "SEA", "HORMUZ", 1900, 6, 90000),
    ("Long Beach", "United States", "Mundra", "India", "AIR", "AIR", 13800, 3, 1200000),
]

_EXPENSE_CATEGORIES = [
    "Freight & Logistics",
    "Raw Materials",
    "Warehousing",
    "Customs & Duties",
    "Salaries",
    "Utilities",
    "Marketing",
]


def _money(low: float, high: float) -> float:
    return round(random.uniform(low, high), 2)


def seed_organization(
    db: Session,
    organization_id: int,
    industry: str | None = None,
) -> dict:
    """Populate one organization with a small realistic dataset.

    Idempotent-ish: if the org already has suppliers we assume it is seeded
    and do nothing. Never raises — returns a summary dict.
    """

    rng = random.Random(organization_id)
    random.seed(organization_id)

    industry = (industry or "General").strip() or "General"

    existing = (
        db.query(Supplier)
        .filter(Supplier.organization_id == organization_id)
        .count()
    )
    if existing:
        return {"skipped": "organization already has data"}

    now = datetime.utcnow()
    summary: dict[str, int] = {}

    # --- suppliers --------------------------------------------------------
    suppliers: list[Supplier] = []
    for name, country, city, lead in _SUPPLIERS:
        s = Supplier(
            organization_id=organization_id,
            name=name,
            contact_email=f"sales@{name.split()[0].lower()}.example",
            category=industry,
            status=rng.choice(["ACTIVE", "ACTIVE", "ACTIVE", "AT_RISK"]),
            country=country,
            city=city,
            lead_time_days=lead,
        )
        db.add(s)
        suppliers.append(s)
    db.flush()
    summary["suppliers"] = len(suppliers)

    # --- products -------------------------------------------------------
    products: list[Product] = []
    for i in range(10):
        p = Product(
            organization_id=organization_id,
            name=f"{industry} SKU {i + 1:02d}",
            category=rng.choice(["Core", "Accessory", "Consumable", "Premium"]),
            unit_price=_money(250, 45000),
        )
        db.add(p)
        products.append(p)
    db.flush()
    summary["products"] = len(products)

    # --- inventory ------------------------------------------------------
    for p in products:
        db.add(
            Inventory(
                organization_id=organization_id,
                product_id=p.id,
                quantity=rng.randint(0, 800),
                reorder_level=120,
                safety_stock=60,
            )
        )
    summary["inventory"] = len(products)

    # --- customers -----------------------------------------------------
    customers: list[Customer] = []
    for i in range(20):
        c = Customer(
            organization_id=organization_id,
            name=f"Customer {i + 1:02d}",
            email=f"buyer{i + 1}@client.example",
        )
        db.add(c)
        customers.append(c)
    db.flush()
    summary["customers"] = len(customers)

    # --- orders + items + revenue transactions ------------------------
    order_count = 0
    for i in range(32):
        when = now - timedelta(days=rng.randint(0, 180), hours=rng.randint(0, 23))
        status = rng.choice(
            ["COMPLETED", "COMPLETED", "COMPLETED", "PENDING", "CANCELLED"]
        )
        order = Order(
            organization_id=organization_id,
            customer_id=rng.choice(customers).id,
            order_number=f"SO-{organization_id:04d}-{i + 1:04d}",
            status=status,
            total_amount=0,
            order_date=when,
        )
        db.add(order)
        db.flush()

        total = 0.0
        for _ in range(rng.randint(1, 4)):
            prod = rng.choice(products)
            qty = rng.randint(1, 12)
            line = qty * float(prod.unit_price)
            total += line
            db.add(
                OrderItem(
                    organization_id=organization_id,
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=float(prod.unit_price),
                    line_total=round(line, 2),
                )
            )
        order.total_amount = round(total, 2)
        order_count += 1

        if status != "CANCELLED":
            db.add(
                Transaction(
                    organization_id=organization_id,
                    transaction_type="REVENUE",
                    amount=round(total, 2),
                    description=f"Payment for {order.order_number}",
                    transaction_date=when,
                )
            )
    summary["orders"] = order_count

    # --- expenses ----------------------------------------------------
    for _ in range(24):
        when = now - timedelta(days=rng.randint(0, 180))
        db.add(
            Expense(
                organization_id=organization_id,
                category=rng.choice(_EXPENSE_CATEGORIES),
                amount=_money(10000, 260000),
                description="Operating expense",
                expense_date=when,
            )
        )
    summary["expenses"] = 24

    # --- supply routes --------------------------------------------------
    routes: list[SupplyRoute] = []
    for idx, (
        o_port,
        o_country,
        d_port,
        d_country,
        mode,
        corridor,
        dist,
        transit,
        freight,
    ) in enumerate(_ROUTES):
        supplier = suppliers[idx % len(suppliers)]
        product = products[idx % len(products)]
        r = SupplyRoute(
            organization_id=organization_id,
            supplier_id=supplier.id,
            product_id=product.id,
            route_name=f"{o_port} → {d_port} via {corridor.replace('_', ' ').title()}",
            origin_country=o_country,
            origin_port=o_port,
            destination_country=d_country,
            destination_port=d_port,
            transport_mode=mode,
            corridor=corridor,
            distance_km=dist,
            transit_days=transit,
            freight_cost=freight,
            risk_level=rng.choice(["LOW", "MEDIUM", "MEDIUM"]),
            status="ACTIVE",
        )
        db.add(r)
        routes.append(r)
    db.flush()
    summary["routes"] = len(routes)

    # --- open purchase orders (drive exposure) ------------------------
    for i, route in enumerate(routes[:3]):
        po = PurchaseOrder(
            organization_id=organization_id,
            supplier_id=route.supplier_id,
            po_number=f"PO-{organization_id:04d}-{i + 1:03d}",
            status="OPEN",
            currency="INR",
            total_amount=_money(400000, 3500000),
            incoterm="FOB",
            order_date=now - timedelta(days=rng.randint(5, 40)),
            expected_date=now + timedelta(days=rng.randint(5, 30)),
        )
        db.add(po)
        db.flush()
        db.add(
            PurchaseOrderLine(
                organization_id=organization_id,
                purchase_order_id=po.id,
                product_id=route.product_id,
                description=f"Line for {po.po_number}",
                quantity=rng.randint(50, 500),
                unit_cost=_money(500, 20000),
            )
        )
    summary["purchase_orders"] = 3

    db.commit()
    logger.info("Seeded org %s: %s", organization_id, summary)
    return summary
