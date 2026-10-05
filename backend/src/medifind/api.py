"""P1 browser APIs. Ownership and expected revision remain server-side."""

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError

from medifind import contracts as c
from medifind.catalog import list_products
from medifind.security import COOKIE, authenticate, database, fail, login, mutate, own
from medifind.tables import inventory, pharmacies, products, sessions

router = APIRouter(prefix="/api/v1")
Connection = Annotated[object, Depends(database)]


@router.post("/auth/login", response_model=c.SessionOut)
def login_route(request: Request, body: c.Login, response: Response):
    return login(request, body, response)


@router.get("/auth/session", response_model=c.SessionOut)
def current_session(request: Request, connection: Connection):
    return authenticate(request, connection)


@router.post("/auth/logout", status_code=204)
def logout(request: Request, connection: Connection):
    auth = mutate(request, connection)
    connection.execute(delete(sessions).where(sessions.c.token_hash == auth["token_hash"]))
    response = Response(status_code=204)
    response.delete_cookie(
        COOKIE,
        path="/",
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="strict",
    )
    return response


@router.get("/catalog", response_model=list[c.ProductOut])
def catalog(request: Request, connection: Connection):
    authenticate(request, connection)
    return list_products(connection)


@router.get("/pharmacies/{pharmacy_id}", response_model=c.PharmacyOut)
def profile(pharmacy_id: UUID, request: Request, connection: Connection):
    own(pharmacy_id, authenticate(request, connection))
    return (
        connection.execute(select(pharmacies).where(pharmacies.c.id == pharmacy_id))
        .mappings()
        .one()
    )


@router.patch("/pharmacies/{pharmacy_id}", response_model=c.PharmacyOut)
def edit_profile(pharmacy_id: UUID, body: c.PharmacyEdit, request: Request, connection: Connection):
    own(pharmacy_id, mutate(request, connection))
    row = (
        connection.execute(
            update(pharmacies)
            .where(
                pharmacies.c.id == pharmacy_id,
                pharmacies.c.revision == body.revision,
            )
            .values(
                **body.model_dump(exclude={"revision"}),
                updated_at=func.clock_timestamp(),
                revision=pharmacies.c.revision + 1,
            )
            .returning(pharmacies)
        )
        .mappings()
        .first()
    )
    if row is None:
        fail(409, "revision_conflict", "Profile changed; reload before editing")
    return row


@router.get("/pharmacies/{pharmacy_id}/inventory", response_model=list[c.InventoryOut])
def own_inventory(pharmacy_id: UUID, request: Request, connection: Connection):
    own(pharmacy_id, authenticate(request, connection))
    return (
        connection.execute(
            select(inventory).where(inventory.c.pharmacy_id == pharmacy_id).order_by(inventory.c.id)
        )
        .mappings()
        .all()
    )


@router.post("/pharmacies/{pharmacy_id}/inventory", response_model=c.InventoryOut, status_code=201)
def add_inventory(
    pharmacy_id: UUID, body: c.InventoryAdd, request: Request, connection: Connection
):
    own(pharmacy_id, mutate(request, connection))
    if not connection.scalar(select(products.c.id).where(products.c.id == body.product_id)):
        fail(404, "product_not_found", "Catalog product not found")
    try:
        return (
            connection.execute(
                insert(inventory)
                .values(
                    id=uuid4(),
                    pharmacy_id=pharmacy_id,
                    **body.model_dump(),
                )
                .returning(inventory)
            )
            .mappings()
            .one()
        )
    except IntegrityError:
        fail(409, "inventory_conflict", "Inventory already exists or changed; reload")


def revision_result(row, connection, pharmacy_id, inventory_id):
    if row is not None:
        return row
    exists = connection.scalar(
        select(inventory.c.id).where(
            inventory.c.id == inventory_id,
            inventory.c.pharmacy_id == pharmacy_id,
        )
    )
    if not exists:
        fail(404, "inventory_not_found", "Own inventory item not found")
    fail(409, "revision_conflict", "Inventory changed; reload before editing")


@router.patch("/pharmacies/{pharmacy_id}/inventory/{inventory_id}", response_model=c.InventoryOut)
def edit_inventory(
    pharmacy_id: UUID,
    inventory_id: UUID,
    body: c.InventoryEdit,
    request: Request,
    connection: Connection,
):
    own(pharmacy_id, mutate(request, connection))
    values = body.model_dump(exclude={"revision"}, exclude_unset=True)
    values.update(updated_at=func.clock_timestamp(), revision=inventory.c.revision + 1)
    if "quantity" in values:
        values["stock_confirmed_at"] = func.clock_timestamp()
    row = (
        connection.execute(
            update(inventory)
            .where(
                inventory.c.id == inventory_id,
                inventory.c.pharmacy_id == pharmacy_id,
                inventory.c.revision == body.revision,
            )
            .values(**values)
            .returning(inventory)
        )
        .mappings()
        .first()
    )
    return revision_result(row, connection, pharmacy_id, inventory_id)


@router.post(
    "/pharmacies/{pharmacy_id}/inventory/{inventory_id}/confirm", response_model=c.InventoryOut
)
def confirm_inventory(
    pharmacy_id: UUID,
    inventory_id: UUID,
    body: c.Revision,
    request: Request,
    connection: Connection,
):
    own(pharmacy_id, mutate(request, connection))
    row = (
        connection.execute(
            update(inventory)
            .where(
                inventory.c.id == inventory_id,
                inventory.c.pharmacy_id == pharmacy_id,
                inventory.c.revision == body.revision,
            )
            .values(
                stock_confirmed_at=func.clock_timestamp(),
                updated_at=func.clock_timestamp(),
                revision=inventory.c.revision + 1,
            )
            .returning(inventory)
        )
        .mappings()
        .first()
    )
    return revision_result(row, connection, pharmacy_id, inventory_id)


@router.delete("/pharmacies/{pharmacy_id}/inventory/{inventory_id}", status_code=204)
def remove_inventory(
    pharmacy_id: UUID,
    inventory_id: UUID,
    body: c.Revision,
    request: Request,
    connection: Connection,
):
    own(pharmacy_id, mutate(request, connection))
    row = (
        connection.execute(
            delete(inventory)
            .where(
                inventory.c.id == inventory_id,
                inventory.c.pharmacy_id == pharmacy_id,
                inventory.c.revision == body.revision,
            )
            .returning(inventory)
        )
        .mappings()
        .first()
    )
    revision_result(row, connection, pharmacy_id, inventory_id)
    return Response(status_code=204)
