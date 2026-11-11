# Library Management System

This Project is a library management system built using FastAPI, Streamlit and MySQL running in docker as seperate containers.

## Architecture
- MySQL - Stores book data and seeds it to FastAPI
- FastAPI - handles the Backend 
- Streamlit - Frontend Dashboard Interface 
- OAuth2 - Token Bearing for one protected endpoint (Delete)

## How to Run:
 1. Create a similar .env file if not created in your system.
 2. in bash or terminal enter: docker compose up --build

You will see:
1. FastAPI Swagger running at localhost:8000/docs
2. Streamlit Dashboard at localhost:8501
3. MySQL is connected can be tested inside swagger docs "chk_connection"

### API Endpoints

- GET /books - Gets a list of all books from our books_data dataset.
- POST /books/{id} - Create or add a new book to our library
- PUT - Update an Existing Book
- POST /token - Get a OAuth2 access token
- DELETE /books/{id} - Delete a book after authenticating from POST / token

## Authorise in swagger docs to access post /token or delete endpoint.
username = admin
password = easypassword

### Examples of working with Streamlit:

1. **You would like to check a list of all books both issued and available in the library** - _Simply click on Load button which would give a result as a pandas dataframe._

2. **You would like to Add a New Book.** - _Simply click on the add book section, carefully enter all the details such as title, author, category and from the dropdown menu select either issued or available, and then click on the add book button. The id is created automatically. You can verify if your book was added by going back to the View Books Section at the top and click on load Books and scroll down you should be able to successfully view your new book in the list._

3. Similarly you can Update a existing book or delete a existing Book.
