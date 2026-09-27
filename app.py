import os

from gymlog import create_app

app = create_app()

if __name__ == "__main__":
    # 0.0.0.0 so it is reachable from outside a container later (Assignment 2)
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
