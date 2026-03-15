from decimal import Decimal
from pathlib import Path
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from tutorials.database_lab.config import lab_database_url
from tutorials.database_lab.models import Student, TransferLog, Wallet


def print_title(title: str) -> None:
    print(f"\n=== {title} ===")


def create_students(session: Session) -> None:
    print_title("Create")

    # 先查再插，避免每次运行脚本都重复插入同样的数据。
    existing = session.execute(
        select(Student).filter(Student.email == "alice@example.com")
    ).scalar_one_or_none()

    if existing is None:
        alice = Student(
            name="Alice",
            email="alice@example.com",
            learning_goal="Learn database basics through project practice",
        )
        bob = Student(
            name="Bob",
            email="bob@example.com",
            learning_goal="Understand CRUD and transactions",
        )
        # add_all 把对象加入当前事务，但真正落库要等 commit。
        session.add_all([alice, bob])
        session.commit()
        print("Inserted Alice and Bob.")
    else:
        print("Sample students already exist.")


def read_students(session: Session) -> None:
    print_title("Read")

    students = session.execute(select(Student).order_by(Student.id)).scalars().all()
    for student in students:
        print(student)


def update_student(session: Session) -> None:
    print_title("Update")

    # 查询出对象后，直接修改属性即可，ORM 会跟踪变化。
    alice = session.execute(
        select(Student).filter(Student.email == "alice@example.com")
    ).scalar_one()
    alice.learning_goal = "Use SQLAlchemy confidently in backend projects"
    session.commit()
    print(f"Updated Alice's goal: {alice.learning_goal}")


def delete_student(session: Session) -> None:
    print_title("Delete")

    bob = session.execute(
        select(Student).filter(Student.email == "bob@example.com")
    ).scalar_one_or_none()
    if bob is None:
        print("Bob is already deleted.")
        return

    session.delete(bob)
    # commit 之后删除才真正生效。
    session.commit()
    print("Deleted Bob.")


def ensure_wallets(session: Session) -> None:
    # 为事务演示准备初始数据。
    owners = {wallet.owner: wallet for wallet in session.execute(select(Wallet)).scalars()}

    if "Alice" not in owners:
        session.add(Wallet(owner="Alice", balance=Decimal("100.00")))
    if "Bob" not in owners:
        session.add(Wallet(owner="Bob", balance=Decimal("50.00")))
    session.commit()


def print_wallets(session: Session, title: str) -> None:
    print_title(title)
    wallets = session.execute(select(Wallet).order_by(Wallet.id)).scalars().all()
    for wallet in wallets:
        print(wallet)


def transfer_money(
    session: Session, from_owner: str, to_owner: str, amount: Decimal, note: str
) -> None:
    # 一次转账其实包含多步数据库操作：
    # 1. 扣钱
    # 2. 加钱
    # 3. 写转账日志
    from_wallet = session.execute(
        select(Wallet).filter(Wallet.owner == from_owner)
    ).scalar_one()
    to_wallet = session.execute(select(Wallet).filter(Wallet.owner == to_owner)).scalar_one()

    if from_wallet.balance < amount:
        # 故意抛出异常，用来演示 rollback。
        raise ValueError(
            f"Insufficient balance: {from_owner} has {from_wallet.balance}, needs {amount}"
        )

    from_wallet.balance -= amount
    to_wallet.balance += amount
    session.add(
        TransferLog(
            from_wallet_id=from_wallet.id,
            to_wallet_id=to_wallet.id,
            amount=amount,
            note=note,
        )
    )


def transaction_demo(session: Session) -> None:
    print_title("Transaction")
    ensure_wallets(session)
    print_wallets(session, "Wallets Before Transfer")

    try:
        transfer_money(
            session,
            from_owner="Alice",
            to_owner="Bob",
            amount=Decimal("30.00"),
            note="Successful transfer demo",
        )
        # 成功时 commit，事务正式落库。
        session.commit()
        print("Committed successful transfer: Alice -> Bob, 30.00")
    except Exception as exc:
        # 如果这里异常，所有未提交修改都会回滚。
        session.rollback()
        print(f"Unexpected error in successful transfer demo: {exc}")

    print_wallets(session, "Wallets After Successful Transfer")

    try:
        transfer_money(
            session,
            from_owner="Alice",
            to_owner="Bob",
            amount=Decimal("1000.00"),
            note="This should fail",
        )
        session.commit()
    except Exception as exc:
        print(f"Transfer failed, rollback triggered: {exc}")
        # 回滚后，Alice 和 Bob 的余额应保持失败前状态。
        session.rollback()

    print_wallets(session, "Wallets After Failed Transfer")

    logs = session.execute(select(TransferLog).order_by(TransferLog.id)).scalars().all()
    print_title("Transfer Logs")
    for log in logs:
        print(log)


def main() -> None:
    engine = create_engine(lab_database_url())

    with Session(engine) as session:
        # 这里故意按“增删改查 + 事务”的学习顺序组织。
        create_students(session)
        read_students(session)
        update_student(session)
        delete_student(session)
        read_students(session)
        transaction_demo(session)

    engine.dispose()


if __name__ == "__main__":
    main()
