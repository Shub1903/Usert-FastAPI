import bcrypt # type: ignore

password = "mysecretpassword"
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed_password)
