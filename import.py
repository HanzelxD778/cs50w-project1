from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import csv

engine = create_engine("postgresql://obsghscguuzowe:3c6e5427738f6b46f3f5cdb586a8b36605b22dbda8641c8967f443e61a22c30a@ec2-35-174-122-153.compute-1.amazonaws.com:5432/de1oes4ebe0rls")
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn":isbn, "title":title, "author":author, "year":year})
        print(f"agregando {title}, {year}")
    db.commit()

if __name__ == "__main__":
    main()