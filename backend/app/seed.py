# app/seed.py
from .database import SessionLocal, Base, engine
from . import models

Base.metadata.create_all(bind=engine)

def main():
    db = SessionLocal()
    if db.query(models.Message).count() > 0:
        print("Messages already exist, skipping seed.")
        return

    msgs = [
        models.Message(
            subject="Refill request for blood pressure medication",
            body="Hi, I am running low on my lisinopril prescription. Can I get a refill before my next appointment?",
            channel="portal",
        ),
        models.Message(
            subject="Billing question about last visit",
            body="I was charged twice for my last consultation. Can someone explain the bill?",
            channel="email",
        ),
        models.Message(
            subject="New chest pain and shortness of breath",
            body="Today I started experiencing chest pain when climbing stairs and some shortness of breath.",
            channel="phone",
        ),
    ]
    db.add_all(msgs)
    db.commit()
    print("Seeded demo messages.")

if __name__ == "__main__":
    main()
