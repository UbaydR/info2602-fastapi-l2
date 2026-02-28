from typing import Annotated
import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command(help= "Initialize the database with a default user (bob)")
def initialize():
    with get_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        bob = User('bob', 'bob@mail.com', 'bobpass') # Create a new user (in memory)
        db.add(bob) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(bob) # Update the user (we use this to get the ID from the db)
        print("Database Initialized")

@cli.command(help= "Get a user by username and print it to the console")
def get_user(username:str):
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command(help = "Get all users and print them")
def get_all_users():
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)

@cli.command(help = "Change a user's email address by username")
def change_email(username: str, new_email:str):
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command(help= "Create a new user with the given username, email and password")
def create_user(username: str, email:str, password: str):
    with get_session() as db: # Get a connection to the database
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            print("Username or email already taken!")
        else:
            print(newuser)

@cli.command(help = "Delete a user by the given username")
def delete_user(username: str):
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')


#exercises

#excerise 1
@cli.command(help= "Find users by partial match of username or email")
def find_user(
    query:Annotated[str,typer.Argument(help = "Partial match for username or email")]
    ):
    with get_session() as db:
        users = db.exec(select(User).where((User.username.contains(query)) | (User.email.contains(query)) )).all()
        if not users:                  
            print(f'No users found matching "{query}"')       
            return                      
        for user in users:              
            print(user)


#excerise 2
@cli.command(help= "List users using pagination with limit and offset")
def paginated_table(
    limit:int=typer.Option(10,help="10 users returned per page."),
    offset:int=typer.Option(0,help="Number of users to skip before starting to return results."),
):
    with get_session() as db:
        users=db.exec(select(User).offset(offset).limit(limit)).all()
        if not users:
            print("No users found")
        for user in users:
            print(user)

if __name__ == "__main__":
    cli()