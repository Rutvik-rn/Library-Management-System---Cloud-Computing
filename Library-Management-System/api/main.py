import os, time
import mysql.connector, csv
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
import hashlib


app = FastAPI(title="Library Management System", version="1.0.0")

load_dotenv()

# Loading environment variables from our env file or "security features lecture"

def load_environment_variables():

    load_dotenv()
    config = {
        "host" : os.getenv("MYSQL_HOST", "mysql"),
        "port" : os.getenv("MYSQL_PORT", "3306"),
        "database" : os.getenv("MYSQL_DB"),
        "user" : os.getenv("MYSQL_USER"),
        "password" : os.getenv("MYSQL_PASSWORD")
    }

    required_vars = ["user","password","database"]
    missing_vars = [var for var in required_vars if not config[var]]
    # to get a clear message to understand what is missing or what caused the error
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please check your .env file."
        )
    
    return config

# connecting to mysql
def connect_mysql(config):

    return mysql.connector.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
    )

# Testing that connection with a get endpoint
@app.get("/chk_connection",
    summary = "Just a simple get endpoint to test mysql connection")
def check_mysql():
    try:
        config =load_environment_variables()
        conn = connect_mysql(config)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()[0]

        cur.execute("SELECT DATABASE();")
        db_name = cur.fetchone()[0]

        cur.execute("SELECT CURRENT_USER();")
        db_user = cur.fetchone()[0]

        cur.close()
        conn.close()
        return{
            "db_connected" :True,
            "query_result": result,
            "host": config["host"],
            "port": config["port"],
            "database": db_name,
            "db_user": db_user,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Error in connection:{e}") 
    
# Need to start mysql first and create the tables later
def wait_mysql(config):
    for _ in range(10):
        try:
            c = connect_mysql(config)
            c.close()
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("SQL Not Ready")

""" 

creating a table in mysql with similar columns to the books.csv (id,title,author,category,status).

id = will be primary key with increament
title = name of the book
author = the author of the book
category = Fiction, Biography, History, Arts, Education, ........
status = issued, available 


"""
def create_books(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255),
            author VARCHAR(255),
            category VARCHAR(255),
            status VARCHAR(20)
        );
        """
    )
    conn.commit()
    cur.close()

# seeding books_csv - count (check table), read rows 

books_csv = os.path.join(os.path.dirname(__file__), "Books_data.csv")

def seed_books(conn):

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM books;")
    count = cur.fetchone()[0]
    if count > 0:
        cur.close()
        return
    
    rows = []
    with open(books_csv, newline="") as f:
        file = csv.DictReader(f)

        for row in file:
            title = row.get("title")
            author = row.get("author")
            category = row.get("category")
            status = row.get("status")

            if title and author and category and status:
                rows.append((title,author,category,status))

    if rows:
        cur.executemany(
            "INSERT INTO books (title, author, category, status) VALUES (%s, %s, %s, %s)",
            rows
        )
        conn.commit()

    cur.close()

# OAuth2 Implementation from hashed password stored in .env file 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
API_USER = os.getenv("API_USER","admin")
API_PASSWORD_HASH = os.getenv("API_PASSWORD_HASH","")
SECRET_KEY = os.getenv("SECRET_KEY","")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ALGORITHM = "HS256"

# Verify Password 
def verify_password(plain_password: str, hashed_password:str) -> bool:
    computed_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return computed_hash == hashed_password

# Create Access Tokens
def create_access_token(data:dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Decode and validate JWT access token 
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def current_user(token: str = Depends(oauth2_scheme)) -> str:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401,detail="Invalid or Expired token")
    username = payload.get("sub")
    return username

@app.post("/token",
    summary = "Get Jwt Token",
    description = "OAUTH2 Password Flow to get bearer token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != API_USER:
        raise HTTPException(status_code=401, detail="Incorrect Username")
    if not verify_password(form_data.password, API_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Incorrect Password")
    access_token = create_access_token({"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

""" Endpoints to get a list of all books, create a new book, add new books , update books and delete books if old."""

# Geting a ist of all the books in our library management system.
@app.get("/books",
    summary = "Get a list of all books in the library management system",
    description = "You get a list of all books currently in your library management system, if updated, deleted or created new books all will update here so can verify here.")
def all_books():
    config = load_environment_variables()
    conn = connect_mysql(config)
    cur = conn.cursor(dictionary = True)
    cur.execute("SELECT * FROM books;")
    book = cur.fetchall()
    cur.close()
    conn.close()
    return book
    

# Getting A book by its ID - basic test of GET endpoint
@app.get("/books/{id}",
    summary = "Fetch any book by id 1 to 61",
    description = "When you enter any number between 1 to 61, which is the book id, this endpoint will fetch you all the details such as the title of the book, the author and its status if it is issued or available.")
def get_book(id: int):
    config = load_environment_variables()
    conn = connect_mysql(config)
    cur = conn.cursor(dictionary = True)
    cur.execute("SELECT id, title, author, category, status FROM books WHERE id=%s", (id,))
    book = cur.fetchone()
    cur.close()
    conn.close()

    if not book:
        raise HTTPException(status_code = 404, detail= "Book Not Found")
    return book

""" 

it will be better to use a Pydantic model for POST endpoints or PUT endpoints as it ensures user enters all the required field, for example with the simple 
function it would crash if user forgets to input lets say "status" while creating a new book. Pydantic helps here by fixing a 
class that would describe our data entry

"""
# First create a class to define data points
class Book_model(BaseModel):
    title:str
    author:str
    category:str
    status:str

# POST endpoint to create a new book with your title, author, and its status. id is automatically created.
@app.post("/books",
    summary = "Create or Add new book to the library management system",
    description = "When you enter all the required strings for title, author, category, status a new book is created with a auto generate id. you can also verify this by going back to the GET books and enter a new id say 62, you will be able to see your book created."
    )
def create_new(book: Book_model):
    config = load_environment_variables()
    conn = connect_mysql(config)
    cur = conn.cursor()
    cur.execute( "INSERT INTO books (title, author, category, status) VALUES (%s, %s, %s, %s)", (book.title,book.author,book.category,book.status))
    conn.commit()
    cur.close()
    conn.close()

    return {"created":True}

# Update a existing book by replacing its author, title, category or status 
@app.put("/books/{id}",
    summary = "Update a book",
    description = "You can update any book by first selecting its id and then updating the values. useful when for example you have a new edition of the same book and you want to replace it. important: have to enter the same author, category or status if you do not want to change that. In a real world example you would have a ISBN number rather than the id.")
def update_book(id:int, book:Book_model):
    config = load_environment_variables()
    conn = connect_mysql(config)
    cur = conn.cursor()
    cur.execute("UPDATE books SET title= %s, author= %s, category= %s, status= %s WHERE id=%s", (book.title,book.author,book.category,book.status, id))
    conn.commit()
    cur.close()
    conn.close()
    return {"updated": True}

# Delete a book by its id
@app.delete("/books/{id}",
    summary = "Delete any book (Protected by token)",
    description = "When you enter any number between 1 to 61, which is the book id, this endpoint will help delete the book from the library management system.")
def delete_book(id:int, user: str= Depends(current_user)):
    config = load_environment_variables()
    conn = connect_mysql(config)
    cur = conn.cursor()
    cur.execute("DELETE FROM books WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"deleted": True}

@app.on_event("startup")
def main():
    print("Library Management System")
    config = load_environment_variables()
    wait_mysql(config)
    conn = connect_mysql(config)
    create_books(conn)
    seed_books(conn)
    conn.close()

