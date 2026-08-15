from typing import Annotated

from db_connection import sql_engine, r_sessions

from sqlalchemy.orm import Session
from sqlalchemy import select, or_, text, update, delete

from endpoints.admin import check_admin
from endpoints.auth import get_or_create_session
from fastapi import APIRouter, HTTPException, status, Depends

from pd_models import TransactionsSchemaPD
from db_models import TransactionsSchemaDB, UsersSchemaDB


router = APIRouter(prefix="/api/v1/transactions")


@router.get("/")
def get_transactions(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    user_id: int | None = None
):
    if (user_id is None) and (not is_admin):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "only admins can view all transactions"
        )
    
    requester_uid = r_sessions.hget(f"ses_{session_id}", "user_id")

    if (user_id is not None) and (not is_admin) and (requester_uid != str(user_id)):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "you can view only your own transactions"
        )

    with Session(sql_engine) as ses:
        stmt = select(TransactionsSchemaDB)
        if user_id is not None:
            stmt = stmt.where( 
                or_(
                    TransactionsSchemaDB.user_from_id == user_id, 
                    TransactionsSchemaDB.user_to_id == user_id
                )
            )
        transactions = ses.scalars(stmt).all()

    return [t for t in transactions]


@router.get("/{transaction_id}")
def get_transaction(
    is_admin: Annotated[bool, Depends(check_admin)],
    transaction_id: int
):
    if not is_admin:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "only admins can view specific transactions"
        )

    with Session(sql_engine) as ses:
        stmt = select(
                    TransactionsSchemaDB
                ).where(
                    TransactionsSchemaDB.transaction_id == transaction_id
                )
        transaction = ses.scalar(stmt)

    if transaction:
        return transaction

    else:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"there is no transaction with {transaction_id=}"
        )
    

def update_user_balance(
    user_id: int,
    db_session: Any,
    delta_res1: int,
    delta_res2: int
):
    stmt = update(
                UsersSchemaDB
            ).where(
                UsersSchemaDB.user_id == user_id
            ).values(
                res1 = UsersSchemaDB.res1 + delta_res1,
                res2 = UsersSchemaDB.res2 + delta_res2,
            )

    db_session.execute(stmt)


@router.post("/")
def create_transaction(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    transaction: TransactionsSchemaPD
):

    requester_uid = r_sessions.hget(f"ses_{session_id}", "user_id")

    if (not is_admin) and (requester_uid != str(transaction.user_from_id)):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "THAT'S ILLEGAL"
        )

    try:
        with Session(sql_engine) as ses:
            update_user_balance(
                user_id    = transaction.user_from_id,
                db_session = ses,
                delta_res1 = (-1) * transaction.res1,
                delta_res2 = (-1) * transaction.res2 
            )

            update_user_balance(
                user_id    = transaction.user_to_id,
                db_session = ses,
                delta_res1 = transaction.res1,
                delta_res2 = transaction.res2 
            )

            transaction_obj = TransactionsSchemaDB(**dict(transaction))
            stmt = ses.add(transaction_obj)

            ses.commit()

            ses.refresh(transaction_obj)

    except Exception as ex:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"can't create transaction: {ex}"    
        )

    return transaction_obj



@router.delete("/{transaction_id}")
def delete_transaction(
    is_admin: Annotated[bool, Depends(check_admin)],
    transaction_id: int
):
    if not is_admin:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "only admins can delete transactions"
        )

    try:
        with Session(sql_engine) as ses:
            
            stmt = select(
                        TransactionsSchemaDB
                    ).where(
                        TransactionsSchemaDB.transaction_id == transaction_id
                    )
            transaction = ses.scalar(stmt)

            update_user_balance(
                user_id    = transaction.user_from_id,
                db_session = ses,
                delta_res1 = transaction.res1,
                delta_res2 = transaction.res2
            )

            update_user_balance(
                user_id    = transaction.user_to_id,
                db_session = ses,
                delta_res1 = (-1) * transaction.res1,
                delta_res2 = (-1) * transaction.res2
            )

            stmt = delete(
                    TransactionsSchemaDB
                ).where(
                    TransactionsSchemaDB.transaction_id == transaction_id
                )
            result = ses.execute(stmt)

            ses.commit()

    except Exception as ex:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"can't delete transaction: {ex}"    
        )

    return {"log": f"deleted {result.rowcount} transactions"}