from fastapi import FastAPI

app = FastAPI(title="Notification Service")

@app.get("/")
def root():
    return {"service": "notification-service"}

