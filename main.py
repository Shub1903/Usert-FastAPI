from fastapi import FastAPI, HTTPException, UploadFile, Form, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import bcrypt
import mysql.connector
import json
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO 
import io 
import hashlib


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Shubh_0307",
    "database": "user_db"
}


app = FastAPI()

  
@validator('email_id')
def email_format(cls, v):
        
        cleaned_email = v.strip()
        
        
        if ' ' in cleaned_email:
            raise ValueError(f"Email address contains spaces: {cleaned_email}")
        
        return cleaned_email


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


class User(BaseModel):
    username: str
    password: str
    email_id: EmailStr
    phone_no: str
    random_path: str

@app.post("/upload")
async def upload_file(file: UploadFile):
    if file.content_type not in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/pdf",
        "application/json",
        "text/plain",
    ]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    content = await file.read()

    
    try:
        users = parse_file(file.content_type, content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")

    
    try:
        save_users_to_db(users)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database Error: {str(e)}")

    return JSONResponse(content={"message": "Upload successful"})


def parse_file(content_type: str, content: bytes):
    parsers = {
        "application/pdf": parse_pdf_content,
        "text/plain": parse_text_content,
        "application/json": parse_json_content,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": parse_docx_content,
    }
    if content_type in parsers:
        return parsers[content_type](content)
    else:
        raise ValueError("Unsupported file format")

def parse_pdf_content(content: bytes):
    pdf_file = io.BytesIO(content)
    reader = PdfReader(pdf_file)
    extracted_text = "".join(page.extract_text() for page in reader.pages)
    return extract_users_from_text(extracted_text)

def parse_text_content(content: bytes):
    text = content.decode("utf-8")
    return extract_users_from_text(text)

def parse_json_content(content: bytes):
    data = json.loads(content.decode("utf-8"))
    return [User(**{key: value for key, value in user.items() if key != "id"}) for user in data]

def parse_docx_content(content: bytes):
    doc = Document(io.BytesIO(content))
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return extract_users_from_text(text)

def extract_users_from_text(text: str):
    users = []
    blocks = text.strip().split("\n\n")  
    for block in blocks:
        user_data = {}
        for line in block.split("\n"):
            if ": " in line:
                try:
                    key, value = line.split(": ", 1)
                    key = key.strip().lower().replace(" ", "_").replace("__", "_")
                    user_data[key] = value.strip()
                except ValueError:
                    continue
        if not all(field in user_data for field in ["username", "password", "email_id", "phone_no", "random_path"]):
            raise ValueError(f"Missing required fields in user block: {block}")
        users.append(User(**{key: value for key, value in user_data.items() if key != "id"}))
    return users

def save_users_to_db(users):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for user in users:
            hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cursor.execute(
                """
                INSERT INTO USER (username, password, email_id, phone_no, random_path)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user.username, hashed_password, user.email_id, user.phone_no, user.random_path),
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


@app.get("/users")
def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM USER")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return users


@app.get("/users/{user_id}")
def get_user_by_id(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM USER WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM USER WHERE id = %s", (user_id,))
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")

    cursor.close()
    conn.close()

    return JSONResponse(content={"message": "User deleted successfully"})


@app.put("/users")
def update_user(email_id: Optional[EmailStr] = None, phone_no: Optional[str] = None, 
                username: Optional[str] = None, password: Optional[str] = None, 
                random_path: Optional[str] = None):
    if not email_id and not phone_no:
        raise HTTPException(status_code=400, detail="Email or Phone number is required")

    conn = get_db_connection()
    cursor = conn.cursor()

    
    update_fields = []
    update_values = []
    if username:
        update_fields.append("username = %s")
        update_values.append(username)
    if password:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        update_fields.append("password = %s")
        update_values.append(hashed_password)
    if random_path:
        update_fields.append("random_path = %s")
        update_values.append(random_path)

    query = "UPDATE USER SET " + ", ".join(update_fields) + " WHERE "
    if email_id:
        query += "email_id = %s"
        update_values.append(email_id)
    elif phone_no:
        query += "phone_no = %s"
        update_values.append(phone_no)

    cursor.execute(query, update_values)
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")

    cursor.close()
    conn.close()

    return JSONResponse(content={"message": "User updated successfully"})

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    random_path: Optional[str] = None

@app.patch("/users")
def update_user(
    email_id: Optional[EmailStr] = None,
    phone_no: Optional[str] = None,
    user_update: UserUpdate = None
):
    if not email_id and not phone_no:
        raise HTTPException(status_code=400, detail="Email or Phone number is required")

    conn = get_db_connection()
    cursor = conn.cursor()

    update_fields = []
    update_values = []

    if user_update.username:
        update_fields.append("username = %s")
        update_values.append(user_update.username)
    if user_update.password:
        hashed_password = bcrypt.hashpw(user_update.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        update_fields.append("password = %s")
        update_values.append(hashed_password)
    if user_update.random_path:
        update_fields.append("random_path = %s")
        update_values.append(user_update.random_path)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    condition = ""
    if email_id:
        condition = "email_id = %s"
        update_values.append(email_id)
    elif phone_no:
        condition = "phone_no = %s"
        update_values.append(phone_no)

    update_query = f"UPDATE USER SET {', '.join(update_fields)} WHERE {condition}"

    try:
        cursor.execute(update_query, update_values)
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User updated successfully"}
    except mysql.connector.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()    

   
@app.get("/")
async def root():
    return {"message": "Welcome to the User API"}

   
