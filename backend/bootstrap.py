"""CLI wrapper — run once before the app (e.g. in the deploy start command):

    python bootstrap.py

Also runs automatically from the app's startup lifespan; see
app/db_bootstrap.py.
"""

from app.db_bootstrap import bootstrap_database

if __name__ == "__main__":
    print("Bootstrapping database...")
    result = bootstrap_database()
    print(f"Done: {result}.")
