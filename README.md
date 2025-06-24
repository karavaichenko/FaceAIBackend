## Quick start
```shell
pip install requirements.txt
```
Create secret key for JWT
```shell
openssl genrsa -out src/certs/private_key.pem 2048
```
```shell
openssl rsa -in src/certs/private_key.pem -outform PEM -pubout -out src/certs/public_key.pem
```
Edit .env file
<br/>
Create database "faceai"
<br/>
Run app
```shell
uvicorn src.main:app
```
 
