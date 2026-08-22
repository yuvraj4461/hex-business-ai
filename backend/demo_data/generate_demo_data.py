import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models import (
    Organization,
    Customer,
    Product,
    Service,
    Supplier,
    Employee,
    Location,
    Order,
    OrderItem,
    Inventory,
    InventoryTransaction,
    Transaction,
    Expense,
)
random.seed(42)  # For reproducibility  
BUSINESSES = [
    {
        "name": "FoodCo",
        "industry": "Food",
    },
    {
        "name": "FashionX",
        "industry": "Clothing",
    },
    {
        "name": "HardwarePro",
        "industry": "Hardware",
    },
    {
        "name": "CloudSoft",
        "industry": "Software",
    },
]
def random_date(days_back: int = 365) -> datetime:
    return datetime.utcnow() - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )


def money(minimum: float, maximum: float) -> Decimal:
    value = random.uniform(minimum, maximum)
    return Decimal(str(round(value, 2)))


def random_name() -> str:
    first_names = [
        "Aarav",
        "Vihaan",
        "Arjun",
        "Rohan",
        "Rahul",
        "Ananya",
        "Priya",
        "Aisha",
        "Ishita",
        "Neha",
    ]

    last_names = [
        "Sharma",
        "Verma",
        "Singh",
        "Kapoor",
        "Gupta",
        "Mehta",
        "Malhotra",
        "Kaur",
    ]

    return f"{random.choice(first_names)} {random.choice(last_names)}"

def get_session() -> Session:
    return SessionLocal()
def create_organizations(db: Session) -> dict[str, Organization]:
    organizations = {}

    for business in BUSINESSES:
        existing = (
            db.query(Organization)
            .filter(
                Organization.name == business["name"]
            )
            .first()
        )

        if existing:
            organizations[business["name"]] = existing
            continue

        organization = Organization(
            name=business["name"],
            industry=business["industry"],
        )

        db.add(organization)
        db.flush()

        organizations[business["name"]] = organization

    db.commit()

    return organizations
def create_customers(
    db: Session,
    organization: Organization,
    count: int = 30,
) -> list[Customer]:

    customers = []

    for index in range(count):

        customer = Customer(
            organization_id=organization.id,
            name=random_name(),
            email=f"customer{index + 1}@{organization.name.lower()}.example",
        )

        db.add(customer)
        customers.append(customer)

    db.flush()

    return customers
PRODUCT_CATALOG = {
    "Food": [
        ("Margherita Pizza", "Pizza"),
        ("Classic Burger", "Burger"),
        ("Pasta Alfredo", "Pasta"),
        ("Veg Sandwich", "Sandwich"),
        ("Cold Coffee", "Beverage"),
        ("French Fries", "Side"),
    ],

    "Clothing": [
        ("Classic T-Shirt", "T-Shirts"),
        ("Oversized Hoodie", "Hoodies"),
        ("Slim Fit Jeans", "Jeans"),
        ("Denim Jacket", "Jackets"),
        ("Cotton Shirt", "Shirts"),
        ("Cargo Pants", "Pants"),
    ],

    "Hardware": [
        ("Mechanical Keyboard", "Peripherals"),
        ("Wireless Mouse", "Peripherals"),
        ("16GB RAM", "Memory"),
        ("1TB SSD", "Storage"),
        ("Gaming GPU", "Graphics"),
        ("650W Power Supply", "Power"),
    ],

    "Software": [
        ("Starter Plan", "Subscription"),
        ("Professional Plan", "Subscription"),
        ("Enterprise Plan", "Subscription"),
        ("Analytics Add-on", "Add-on"),
        ("Security Add-on", "Add-on"),
        ("API Package", "Add-on"),
    ],
}
def create_products(
    db: Session,
    organization: Organization,
) -> list[Product]:

    catalog = PRODUCT_CATALOG[
        organization.industry
    ]

    products = []

    for name, category in catalog:

        product = Product(
            organization_id=organization.id,
            name=name,
            category=category,
            unit_price=money(200, 50000),
        )

        db.add(product)
        products.append(product)

    db.flush()

    return products
SERVICE_CATALOG = {
    "Food": [
        ("Catering Service", "Catering"),
        ("Home Delivery", "Delivery"),
    ],

    "Clothing": [
        ("Custom Stitching", "Customization"),
        ("Personal Styling", "Styling"),
    ],

    "Hardware": [
        ("Installation Service", "Installation"),
        ("Repair Service", "Repair"),
    ],

    "Software": [
        ("Implementation Service", "Professional Services"),
        ("Technical Support", "Support"),
        ("Training Service", "Training"),
    ],
}
def create_services(
    db: Session,
    organization: Organization,
) -> list[Service]:

    services = []

    for name, category in SERVICE_CATALOG[
        organization.industry
    ]:

        service = Service(
            organization_id=organization.id,
            name=name,
            category=category,
            price=money(500, 100000),
        )

        db.add(service)
        services.append(service)

    db.flush()

    return services
def create_suppliers(
    db: Session,
    organization: Organization,
    count: int = 5,
) -> list[Supplier]:

    suppliers = []

    for index in range(count):

        supplier = Supplier(
            organization_id=organization.id,
            name=(
                f"{organization.industry} Supplier "
                f"{index + 1}"
            ),
            contact_email=(
                f"supplier{index + 1}"
                f"@{organization.name.lower()}.example"
            ),
            category=organization.industry,
            status=random.choice(
                ["ACTIVE", "ACTIVE", "ACTIVE", "AT_RISK"]
            ),
        )

        db.add(supplier)
        suppliers.append(supplier)

    db.flush()

    return suppliers
def create_employees(
    db: Session,
    organization: Organization,
    count: int = 10,
) -> list[Employee]:

    departments = [
        "Sales",
        "Finance",
        "Operations",
        "Marketing",
        "Support",
        "Management",
    ]

    employees = []

    for index in range(count):

        name = random_name()

        employee = Employee(
            organization_id=organization.id,
            name=name,
            email=(
                f"employee{index + 1}"
                f"@{organization.name.lower()}.example"
            ),
            department=random.choice(departments),
            role=random.choice(
                [
                    "Manager",
                    "Executive",
                    "Associate",
                    "Specialist",
                ]
            ),
            status="ACTIVE",
        )

        db.add(employee)
        employees.append(employee)

    db.flush()

    return employees
def create_locations(
    db: Session,
    organization: Organization,
) -> list[Location]:

    locations = [
        ("Head Office", "Chandigarh", "India", "OFFICE"),
        ("Main Warehouse", "Delhi", "India", "WAREHOUSE"),
    ]

    if organization.industry == "Food":
        locations.append(
            (
                "Restaurant Branch",
                "Mohali",
                "India",
                "RESTAURANT",
            )
        )

    elif organization.industry == "Clothing":
        locations.append(
            (
                "Retail Store",
                "Chandigarh",
                "India",
                "STORE",
            )
        )

    elif organization.industry == "Hardware":
        locations.append(
            (
                "Production Unit",
                "Baddi",
                "India",
                "FACTORY",
            )
        )

    elif organization.industry == "Software":
        locations.append(
            (
                "Development Center",
                "Bengaluru",
                "India",
                "OFFICE",
            )
        )

    result = []

    for name, city, country, location_type in locations:

        location = Location(
            organization_id=organization.id,
            name=name,
            city=city,
            country=country,
            location_type=location_type,
        )

        db.add(location)
        result.append(location)

    db.flush()

    return result
def create_orders(
    db: Session,
    organization: Organization,
    customers: list[Customer],
    locations: list[Location],
    products: list[Product],
    services: list[Service],
    count: int = 60,
) -> list[Order]:

    orders = []

    for index in range(count):

        order = Order(
            organization_id=organization.id,
            customer_id=random.choice(customers).id,
            location_id=random.choice(locations).id,
            order_number=(
                f"{organization.name.upper()[:4]}"
                f"-{index + 1:05d}"
            ),
            status=random.choice(
                [
                    "COMPLETED",
                    "COMPLETED",
                    "COMPLETED",
                    "PENDING",
                    "CANCELLED",
                ]
            ),
            total_amount=Decimal("0.00"),
            order_date=random_date(),
        )

        db.add(order)
        orders.append(order)

    db.flush()

    return orders
def create_order_items(
    db: Session,
    organization: Organization,
    orders: list[Order],
    products: list[Product],
    services: list[Service],
) -> None:

    for order in orders:

        item_count = random.randint(1, 3)
        total = Decimal("0.00")

        for _ in range(item_count):

            use_product = (
                len(products) > 0
                and (
                    len(services) == 0
                    or random.random() > 0.25
                )
            )

            if use_product:
                product = random.choice(products)

                quantity = random.randint(1, 5)
                unit_price = Decimal(
                    str(product.unit_price)
                )

                product_id = product.id
                service_id = None

            else:
                service = random.choice(services)

                quantity = 1
                unit_price = Decimal(
                    str(service.price)
                )

                product_id = None
                service_id = service.id

            line_total = (
                unit_price * quantity
            )

            item = OrderItem(
                organization_id=organization.id,
                order_id=order.id,
                product_id=product_id,
                service_id=service_id,
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
            )

            db.add(item)

            total += line_total

        order.total_amount = total

    db.flush()
def create_inventory(
    db: Session,
    organization: Organization,
    products: list[Product],
    locations: list[Location],
) -> list[Inventory]:

    inventories = []

    inventory_locations = [
        location
        for location in locations
        if location.location_type
        in ["WAREHOUSE", "STORE", "RESTAURANT", "FACTORY"]
    ]

    if not inventory_locations:
        inventory_locations = locations

    for product in products:

        location = random.choice(
            inventory_locations
        )

        inventory = Inventory(
            organization_id=organization.id,
            product_id=product.id,
            location_id=location.id,
            quantity=random.randint(20, 500),
            reorder_level=random.randint(20, 100),
            safety_stock=random.randint(10, 50),
        )

        db.add(inventory)
        inventories.append(inventory)

    db.flush()

    return inventories
def create_inventory_transactions(
    db: Session,
    organization: Organization,
    products: list[Product],
    locations: list[Location],
    count: int = 100,
) -> None:

    for _ in range(count):

        product = random.choice(products)
        location = random.choice(locations)

        transaction = InventoryTransaction(
            organization_id=organization.id,
            product_id=product.id,
            location_id=location.id,
            transaction_type=random.choice(
                [
                    "PURCHASE",
                    "SALE",
                    "RETURN",
                    "ADJUSTMENT",
                ]
            ),
            quantity=random.randint(1, 50),
            created_at=random_date(),
        )

        db.add(transaction)

    db.flush()
def create_transactions(
    db: Session,
    organization: Organization,
    orders: list[Order],
) -> None:

    for order in orders:

        if order.status != "COMPLETED":
            continue

        transaction = Transaction(
            organization_id=organization.id,
            transaction_type="REVENUE",
            amount=order.total_amount,
            description=(
                f"Revenue from {order.order_number}"
            ),
            transaction_date=order.order_date,
        )

        db.add(transaction)

    db.flush()
def create_expenses(
    db: Session,
    organization: Organization,
    count: int = 25,
) -> None:

    categories = [
        "Salaries",
        "Marketing",
        "Rent",
        "Utilities",
        "Logistics",
        "Software",
        "Maintenance",
    ]

    for _ in range(count):

        expense = Expense(
            organization_id=organization.id,
            category=random.choice(categories),
            amount=money(1000, 100000),
            description="Demo business expense",
            expense_date=random_date(),
        )

        db.add(expense)

    db.flush()
def generate_all():
    db = get_session()

    try:

        organizations = create_organizations(db)

        for name, organization in organizations.items():

            print(
                f"\nGenerating data for "
                f"{organization.name}"
                f" ({organization.industry})..."
            )

            customers = create_customers(
                db,
                organization,
                count=30,
            )

            products = create_products(
                db,
                organization,
            )

            services = create_services(
                db,
                organization,
            )

            suppliers = create_suppliers(
                db,
                organization,
                count=5,
            )

            employees = create_employees(
                db,
                organization,
                count=10,
            )

            locations = create_locations(
                db,
                organization,
            )

            orders = create_orders(
                db,
                organization,
                customers,
                locations,
                products,
                services,
                count=60,
            )

            create_order_items(
                db,
                organization,
                orders,
                products,
                services,
            )

            create_inventory(
                db,
                organization,
                products,
                locations,
            )

            create_inventory_transactions(
                db,
                organization,
                products,
                locations,
                count=100,
            )

            create_transactions(
                db,
                organization,
                orders,
            )

            create_expenses(
                db,
                organization,
                count=25,
            )

            db.commit()

            print(
                f"✓ {organization.name} generated"
            )

        print(
            "\n✓ All demo business data generated!"
        )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    generate_all()