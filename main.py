from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime
import croniter

app  = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        'http://localhost:3000',
        "https://decrontab.vercel.app",  # Remove trailing slash
        "https://backend-decrontab.onrender.com"  # Add your Render URL when you get it
    ],
    allow_credentials = True,
    allow_methods = ["POST", "GET"],  # Added GET for presets endpoint
    allow_headers = ["*"]
)

class CronRequest(BaseModel):
    minutes: str
    hours: str
    day_of_month: str
    month: str
    day_of_week: str
    command: Optional[str] = ""

@app.post("/api/v1/validate-crontab")
async def validate_cron(cron: CronRequest):
    try:
        expression  = f"{cron.minutes} {cron.hours} {cron.day_of_month} {cron.month} {cron.day_of_week}"

        base = datetime.now()
        iterator = croniter.croniter(expression, base)

        next_dates = [
            iterator.get_next(datetime).strftime("%Y-%m-%d %H:%M:%S")

            for _ in range(5)
        ]

        return {
            "valid": True,
            "expression" : expression,
            "command": cron.command,
            "next_executions": next_dates,
            "explanation": explain_cron(expression)
        }
    except Exception as e:
        raise HTTPException(status_code = 400,
                            detail = str(e))
    
def explain_cron(expression: str) -> str:
    parts = expression.split()
    fields = ["minute", "hour", "day of month", "month", "day of week"]

    explanation = []

    for value, field in zip(parts, fields):
        if value == "*":
            explanation.append(f"every {field}")
        elif "/" in value:
            base, interval = value.split("/")
            explanation.append(f"every {interval} {field} (s)")
        elif "-" in value:
            start, end = value.split("-")
            explanation.append(f"{field}s from {start} to {end}")
        elif "," in value:
            values = value.split(",")
            explanation.append(f"{field}s at {', '.join(values)}")
        else:
            explanation.append(f"at {field} {value}")
    
    return " | ".join(explanation)

@app.get("/api/presets")
async def get_presets():
    return {
        "common_patterns": [
            {
                "name": "Every minute",
                "expression": "* * * * *"
            },
            {
                "name": "Every hour",
                "expression": "0 * * * *"
            },
            {
                "name": "Every day at midnight",
                "expression": "0 0 * * *"
            },
            {
                "name": "Every Monday at 9 AM",
                "expression": "0 9 * * 1"
            },
            {
                "name": "Every weekday",
                "expression": "0 0 * * 1-5"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)