from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from decimal import Decimal

opening_balance: Mapped[Decimal] = mapped_column(
    Numeric(12, 2),
    default=Decimal("0.00"),
    nullable=False,
)

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    account_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )


    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")