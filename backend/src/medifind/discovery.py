"""Presentation-specific inventory, approximate geography and confirmation freshness."""

import math
from datetime import datetime, timedelta

from sqlalchemy import select

from medifind.tables import inventory, pharmacies

EARTH_RADIUS_KM = 6371.0088


def haversine(lat1, lon1, lat2, lon2):
    coordinates = [float(x) for x in (lat1, lon1, lat2, lon2)]
    if any(not math.isfinite(x) for x in coordinates):
        raise ValueError("Finite coordinates required")
    if not (
        -90 <= coordinates[0] <= 90
        and -90 <= coordinates[2] <= 90
        and -180 <= coordinates[1] <= 180
        and -180 <= coordinates[3] <= 180
    ):
        raise ValueError("Coordinates out of range")
    p1, l1, p2, l2 = map(math.radians, coordinates)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2
    a = min(1.0, max(0.0, a))
    return 2 * EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def freshness(confirmed: datetime | None, now: datetime, hours: int) -> str:
    if confirmed is None or confirmed.tzinfo is None or now.tzinfo is None:
        return "UNKNOWN"
    age = now - confirmed
    if age < timedelta(0):
        return "UNKNOWN"
    return "FRESH" if age <= timedelta(hours=hours) else "STALE"


def rank_stock(rows: list[dict], *, sort_by="distance") -> list[dict]:
    order = {"FRESH": 0, "STALE": 1, "UNKNOWN": 2}
    if sort_by == "price":

        def key(r):
            return (
                order[r["freshness"]],
                r["price"],
                r["distance_km"],
                str(r["pharmacy_id"]),
                str(r["inventory_id"]),
            )
    else:

        def key(r):
            return (
                order[r["freshness"]],
                r["distance_km"],
                str(r["pharmacy_id"]),
                str(r["inventory_id"]),
            )

    return sorted(rows, key=key)


def nearby_stock(connection, request, now, *, fresh_hours=24):
    statement = (
        select(
            inventory.c.id.label("inventory_id"),
            inventory.c.pharmacy_id,
            inventory.c.quantity,
            inventory.c.price,
            inventory.c.currency,
            inventory.c.sale_basis,
            inventory.c.stock_confirmed_at,
            pharmacies.c.name,
            pharmacies.c.location_label,
            pharmacies.c.latitude,
            pharmacies.c.longitude,
            pharmacies.c.synthetic,
        )
        .join(pharmacies, inventory.c.pharmacy_id == pharmacies.c.id)
        .where(
            inventory.c.product_id == request.product_id,
            inventory.c.quantity > 0,
            pharmacies.c.active.is_(True),
        )
    )
    if request.sort_by == "price":
        statement = statement.where(
            inventory.c.sale_basis == request.price_basis, inventory.c.currency == "PKR"
        )
    rows = []
    for source in connection.execute(statement).mappings():
        row = dict(source)
        distance = haversine(request.latitude, request.longitude, row["latitude"], row["longitude"])
        if (
            distance > request.radius_km
        ):  # Compare full precision; display rounding is not filtering.
            continue
        state = freshness(row["stock_confirmed_at"], now, fresh_hours)
        if state != "FRESH" and not request.include_unconfirmed:
            continue
        rows.append(
            dict(
                **row,
                distance_km=distance,
                freshness=state,
                availability="RECENT_STOCK_REPORT" if state == "FRESH" else "UNCONFIRMED_REPORT",
            )
        )
    return rank_stock(rows, sort_by=request.sort_by)
