from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Database_setup import Base, Items, Category

engine = create_engine('sqlite:///itemsdb.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()

Category1 = Category(name="3d Printing")

session.add(Category1)
session.commit()

Item1 = Items(
    name="CR10",  description="A mid level printer with large print space",
    category=Category1)
session.add(Item1)
session.commit()
Item2 = Items(
    name="MonoPrice Mini",
    description="An entry level printer with small print space",
    category=Category1)
session.add(Item2)
session.commit()
Item1 = Items(
    name="Hatchbox Filament",  description="A popular filament",
    category=Category1)
session.add(Item1)
session.commit()


# Start of second category

Category2 = Category(name="Shooting")

session.add(Category2)
session.commit()

Item3 = Items(name="Remington 870",
              description="A classic all round shotgun\
              perfect for target shooting", category=Category2)
session.add(Item3)
session.commit()
Item4 = Items(name="Ruger Mark iv 22/45 Lite",  description="A competitive\
              shooting pistol from rugers line of target pistols",
              category=Category2)
session.add(Item4)
session.commit()
Item3 = Items(name="Smith and Wesson Governor",
              description="A multi purpose revolver, commonly\
              used as a trail gun for protection against wild animals",
              category=Category2)
session.add(Item3)
session.commit()
print ("The Data has been added to the database")
