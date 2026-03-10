#!/usr/bin/env python3
"""
export_bible_sqlite.py – Export BibleEngine MySQL tables to a local SQLite file.

Run this on the VPS where MySQL is running:
  python3 export_bible_sqlite.py --host localhost --user root --password PASS --database bibleengine --output bible.sqlite

Then copy bible.sqlite to: devotion_tts/assets/bible/bible.sqlite

The output SQLite has a single table:
  verses(book INT, chapter INT, verse INT, cuvt TEXT, ncvs TEXT, ccsb TEXT, clbs TEXT)
  - cuvt = 和合本 (CUV Traditional)
  - ncvs = 新譯本 (CNV)
  - ccsb = 標準譯本 (CSBS)
  - clbs = 當代譯本 (CCB / 當代聖經)
"""

import argparse
import sqlite3
import sys

def main():
    parser = argparse.ArgumentParser(description="Export BibleEngine MySQL to SQLite")
    parser.add_argument("--host", default="localhost", help="MySQL host")
    parser.add_argument("--port", type=int, default=3306, help="MySQL port")
    parser.add_argument("--user", default="root", help="MySQL user")
    parser.add_argument("--password", default="", help="MySQL password")
    parser.add_argument("--database", default="bibleengine", help="MySQL database name")
    parser.add_argument("--output", "-o", default="bible.sqlite", help="Output SQLite file")
    args = parser.parse_args()

    # Try importing MySQL connector
    try:
        import pymysql
        connect = lambda: pymysql.connect(
            host=args.host, port=args.port,
            user=args.user, password=args.password,
            database=args.database, charset="utf8mb4"
        )
    except ImportError:
        try:
            import mysql.connector
            connect = lambda: mysql.connector.connect(
                host=args.host, port=args.port,
                user=args.user, password=args.password,
                database=args.database, charset="utf8mb4"
            )
        except ImportError:
            print("❌ Neither pymysql nor mysql-connector-python found.")
            print("   Install one: pip install pymysql")
            sys.exit(1)

    # Translation tables to export
    TRANSLATIONS = {
        "cuvt": "bible_book_cuvt",   # 和合本 (Traditional)
        "ncvs": "bible_book_ncvs",   # 新譯本
        "ccsb": "bible_book_ccsb",   # 標準譯本
        "clbs": "bible_book_clbs",   # 當代譯本
    }

    print(f"Connecting to MySQL {args.host}:{args.port}/{args.database}...")
    mysql_conn = connect()
    mysql_cur = mysql_conn.cursor()

    # Create SQLite database
    print(f"Creating SQLite: {args.output}")
    sqlite_conn = sqlite3.connect(args.output)
    sqlite_cur = sqlite_conn.cursor()

    sqlite_cur.execute("DROP TABLE IF EXISTS verses")
    sqlite_cur.execute("""
        CREATE TABLE verses (
            book INTEGER NOT NULL,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            cuvt TEXT,
            ncvs TEXT,
            ccsb TEXT,
            clbs TEXT,
            PRIMARY KEY (book, chapter, verse)
        )
    """)

    # First, get all (book, chapter, verse) from bible_books
    print("Reading verse index from bible_books...")
    mysql_cur.execute("SELECT book, chapter, verse FROM bible_books ORDER BY book, chapter, verse")
    all_verses = mysql_cur.fetchall()
    print(f"  Found {len(all_verses)} verses")

    # Build a dict: (book, chapter, verse) → {cuvt: ..., ncvs: ..., ccsb: ..., clbs: ...}
    verse_data = {}
    for book, chapter, verse in all_verses:
        verse_data[(book, chapter, verse)] = {"cuvt": None, "ncvs": None, "ccsb": None, "clbs": None}

    # Load each translation
    for code, table_name in TRANSLATIONS.items():
        print(f"Reading {code} from {table_name}...")
        try:
            mysql_cur.execute(f"SELECT book, chapter, verse, Scripture FROM {table_name}")
            rows = mysql_cur.fetchall()
            count = 0
            for book, chapter, verse, text in rows:
                key = (book, chapter, verse)
                if key in verse_data:
                    verse_data[key][code] = text
                    count += 1
                else:
                    # Verse exists in translation but not in bible_books — add it
                    verse_data[key] = {"cuvt": None, "ncvs": None, "ccsb": None, "clbs": None}
                    verse_data[key][code] = text
                    count += 1
            print(f"  Loaded {count} verses for {code}")
        except Exception as e:
            print(f"  ⚠️ Error reading {table_name}: {e}")
            print(f"  Skipping {code}")

    # Insert into SQLite
    print("Writing to SQLite...")
    batch = []
    for (book, chapter, verse), translations in sorted(verse_data.items()):
        batch.append((
            book, chapter, verse,
            translations["cuvt"],
            translations["ncvs"],
            translations["ccsb"],
            translations["clbs"],
        ))

    sqlite_cur.executemany(
        "INSERT OR REPLACE INTO verses (book, chapter, verse, cuvt, ncvs, ccsb, clbs) VALUES (?, ?, ?, ?, ?, ?, ?)",
        batch
    )

    # Create indexes
    sqlite_cur.execute("CREATE INDEX IF NOT EXISTS idx_book_chapter ON verses(book, chapter)")

    sqlite_conn.commit()

    # Stats
    sqlite_cur.execute("SELECT COUNT(*) FROM verses")
    total = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT COUNT(*) FROM verses WHERE cuvt IS NOT NULL")
    cuvt_count = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT COUNT(*) FROM verses WHERE ncvs IS NOT NULL")
    ncvs_count = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT COUNT(*) FROM verses WHERE ccsb IS NOT NULL")
    ccsb_count = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT COUNT(*) FROM verses WHERE clbs IS NOT NULL")
    clbs_count = sqlite_cur.fetchone()[0]

    print(f"\n✅ Export complete: {args.output}")
    print(f"   Total verses: {total}")
    print(f"   cuvt (和合本): {cuvt_count}")
    print(f"   ncvs (新譯本): {ncvs_count}")
    print(f"   ccsb (標準譯本): {ccsb_count}")
    print(f"   clbs (當代譯本): {clbs_count}")
    print(f"\nCopy this file to: devotion_tts/assets/bible/bible.sqlite")

    mysql_conn.close()
    sqlite_conn.close()


if __name__ == "__main__":
    main()
