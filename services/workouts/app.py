import os

from workouts import create_app

app = create_app()

if __name__ == "__main__":
    # 0.0.0.0 so it is reachable from outside the container
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
