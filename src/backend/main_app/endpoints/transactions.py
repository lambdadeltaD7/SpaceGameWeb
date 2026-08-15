from fastapi import APIRouter, HTTPException, status, Depends

from typing import Annotated

from db_connection import sql_engine, r_sessions

from sqlalchemy.orm import Session
from sqlalchemy import select, or_, text, update, delete

from endpoints.auth import get_or_create_session
from endpoints.admin import check_admin

from db_models import TransactionsSchemaDB, UsersSchemaDB
from pd_models import TransactionsSchemaPD

router = APIRouter(prefix="/api/v1/transactions")


@router.get("/")
def get_transactions(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    user_id: int | None = None
):
    if (user_id is None) and (not is_admin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="only admins can view all transactions"
        )
    
    requester_uid = r_sessions.hget(f"ses_{session_id}", "user_id")

    if (user_id is not None) and (not is_admin) and (requester_uid != str(user_id)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="you can view only your own transactions"
        )

    with Session(sql_engine) as ses:
        stmt = select(TransactionsSchemaDB)
        if user_id is not None:
            stmt = stmt.where( 
                or_(
                    TransactionsSchemaDB.user_from_id==user_id, 
                    TransactionsSchemaDB.user_to_id==user_id
                )
            )
        result = ses.scalars(stmt).all()
    return [t for t in result]


@router.get("/{transaction_id}")
def get_transaction(
    is_admin: Annotated[bool, Depends(check_admin)],
    transaction_id: int
):
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="only admins can view specific transactions"
        )

    with Session(sql_engine) as ses:
        stmt = select(TransactionsSchemaDB).where(TransactionsSchemaDB.transaction_id==transaction_id)
        result = ses.scalar(stmt)
    if result:
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"there is no transaction with {transaction_id=}"
        )
    


@router.post("/")
def create_transaction(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    transaction: TransactionsSchemaPD
):

    requester_uid = r_sessions.hget(f"ses_{session_id}", "user_id")

    if (not is_admin) and (requester_uid != str(transaction.user_from_id)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="THAT'S ILLEGAL"
        )
    

    try:
        with Session(sql_engine) as ses:
            stmt = update(
                UsersSchemaDB
            ).where(
                UsersSchemaDB.user_id == transaction.user_from_id
            ).values(
                res1 = UsersSchemaDB.res1 - transaction.res1,
                res2 = UsersSchemaDB.res2 - transaction.res2,
            )        
            ses.execute(stmt)

            stmt = update(
                UsersSchemaDB
            ).where(
                UsersSchemaDB.user_id == transaction.user_to_id
            ).values(
                res1 = UsersSchemaDB.res1 + transaction.res1,
                res2 = UsersSchemaDB.res2 + transaction.res2,
            )        
            ses.execute(stmt)

            transaction_obj = TransactionsSchemaDB(**dict(transaction))
            stmt = ses.add(transaction_obj)

            ses.commit()

            ses.refresh(transaction_obj)

    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="only admins can delete transactions"
        )

    try:
        with Session(sql_engine) as ses:
            
            stmt = select(TransactionsSchemaDB).where(TransactionsSchemaDB.transaction_id==transaction_id)
            transaction = ses.scalar(stmt)

            stmt = update(
                UsersSchemaDB
            ).where(
                UsersSchemaDB.user_id == transaction.user_from_id
            ).values(
                res1 = UsersSchemaDB.res1 + transaction.res1,
                res2 = UsersSchemaDB.res2 + transaction.res2,
            )        
            ses.execute(stmt)

            stmt = update(
                UsersSchemaDB
            ).where(
                UsersSchemaDB.user_id == transaction.user_to_id
            ).values(
                res1 = UsersSchemaDB.res1 - transaction.res1,
                res2 = UsersSchemaDB.res2 - transaction.res2,
            )        
            ses.execute(stmt)


            stmt = delete(
                TransactionsSchemaDB
            ).where(
                TransactionsSchemaDB.transaction_id == transaction_id
            )
            result = ses.execute(stmt)

            ses.commit()

    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"can't delete transaction: {ex}"    
        )

    return {"log": f"deleted {result.rowcount} transactions"}