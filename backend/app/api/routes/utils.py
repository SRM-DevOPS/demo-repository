from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic.networks import EmailStr
from sqlalchemy import text

from app.api.deps import get_current_active_superuser, SessionDep
from app.models import Message
from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["utils"])


@router.get("/search-user-vulnerable/", dependencies=[Depends(get_current_active_superuser)])
def search_user_vulnerable(session: SessionDep, email: str = Query(...)) -> Any:
    """
    Vulnerable search endpoint for demonstration (SQL Injection).
    """
    # DANGER: Directly using f-string to build a query from user input is highly vulnerable to SQLi.
    query = f"SELECT * FROM user WHERE email = '{email}'"
    result = session.execute(text(query)).all()
    return result


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True
