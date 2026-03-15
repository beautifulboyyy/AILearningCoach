from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from tutorials.database_lab.config import LAB_SCHEMA


class Base(DeclarativeBase):
    # 所有 ORM 模型的共同基类。
    pass


class Student(Base):
    # 这个类会映射成 lab.students 表。
    __tablename__ = "students"
    __table_args__ = {"schema": LAB_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    learning_goal: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"Student(id={self.id}, name={self.name}, email={self.email})"


class Wallet(Base):
    # 钱包表专门用于演示事务。
    __tablename__ = "wallets"
    __table_args__ = {"schema": LAB_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    outgoing_logs: Mapped[list["TransferLog"]] = relationship(
        "TransferLog",
        foreign_keys="TransferLog.from_wallet_id",
        back_populates="from_wallet",
    )
    incoming_logs: Mapped[list["TransferLog"]] = relationship(
        "TransferLog",
        foreign_keys="TransferLog.to_wallet_id",
        back_populates="to_wallet",
    )

    def __repr__(self) -> str:
        return f"Wallet(id={self.id}, owner={self.owner}, balance={self.balance})"


class TransferLog(Base):
    # 转账日志表，用来记录一次事务里产生的业务记录。
    __tablename__ = "transfer_logs"
    __table_args__ = {"schema": LAB_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_wallet_id: Mapped[int] = mapped_column(
        ForeignKey(f"{LAB_SCHEMA}.wallets.id"), nullable=False
    )
    to_wallet_id: Mapped[int] = mapped_column(
        ForeignKey(f"{LAB_SCHEMA}.wallets.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    note: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    from_wallet: Mapped[Wallet] = relationship(
        "Wallet", foreign_keys=[from_wallet_id], back_populates="outgoing_logs"
    )
    to_wallet: Mapped[Wallet] = relationship(
        "Wallet", foreign_keys=[to_wallet_id], back_populates="incoming_logs"
    )

    def __repr__(self) -> str:
        return (
            "TransferLog("
            f"id={self.id}, from_wallet_id={self.from_wallet_id}, "
            f"to_wallet_id={self.to_wallet_id}, amount={self.amount})"
        )
