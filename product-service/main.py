from fastapi import FastAPI

app = FastAPI(title="Product Service")

@app.get("/")
def root():
    return {"service": "product-service"}

