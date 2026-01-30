from fastapi import FastAPI

app = FastAPI(title="Payment Service")

@app.get("/")
def root():
    return {"service": "payment-service"}

