from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.supply_route import SupplyRoute
from app.models.user import User
from app.security.dependencies import require_permission


router = APIRouter(
    prefix="/routes",
    tags=["Routes"],
)


@router.get("")
def get_routes(
    current_user: User = Depends(
        require_permission("view_analytics")
    ),
    db: Session = Depends(get_db),
):
    organization_id = (
        current_user.organization_id
    )

    routes = (
        db.query(
            SupplyRoute,
            Supplier,
            Product,
        )
        .join(
            Supplier,
            Supplier.id
            == SupplyRoute.supplier_id,
        )
        .outerjoin(
            Product,
            Product.id
            == SupplyRoute.product_id,
        )
        .filter(
            SupplyRoute.organization_id
            == organization_id,
        )
        .order_by(
            SupplyRoute.id.desc()
        )
        .all()
    )

    result = []

    for route, supplier, product in routes:
        result.append(
            {
                "id": route.id,
                "route_name":
                    route.route_name,

                "origin_country":
                    route.origin_country,

                "origin_port":
                    route.origin_port,

                "destination_country":
                    route.destination_country,

                "destination_port":
                    route.destination_port,

                "transport_mode":
                    route.transport_mode,

                "corridor":
                    route.corridor,

                "distance_km":
                    float(
                        route.distance_km
                    ),

                "transit_days":
                    route.transit_days,

                "freight_cost":
                    float(
                        route.freight_cost
                    ),

                "risk_level":
                    route.risk_level,

                "status":
                    route.status,

                "supplier": {
                    "id":
                        supplier.id,

                    "name":
                        supplier.name,
                },

                "product": (
                    {
                        "id":
                            product.id,

                        "name":
                            product.name,
                    }
                    if product
                    else None
                ),
            }
        )

    return {
        "organization_id":
            organization_id,

        "routes":
            result,

        "count":
            len(result),
    }