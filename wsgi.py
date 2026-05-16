from app import app

if __name__ == "__main__":
    # Local dev only; production should use gunicorn
    app.run()

