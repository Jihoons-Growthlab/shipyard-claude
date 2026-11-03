import argparse

from .db import connect, migrate
from .seed import seed_hulls, seed_plans, seed_system


def main() -> None:
    p = argparse.ArgumentParser(prog="app.cli")
    sub = p.add_subparsers(dest="cmd", required=True)
    init = sub.add_parser("init-db", help="apply migrations (and optional demo seed)")
    init.add_argument("--seed", action="store_true")
    a = p.parse_args()
    conn = connect()
    try:
        print("applied:", migrate(conn) or "none")
        if a.seed:
            seed_system(conn)
            seed_hulls(conn)
            seed_plans(conn)
            print("seeded system data")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
