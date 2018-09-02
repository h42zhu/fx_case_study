import sqlite3
import os
import csv
import datetime as dt

FILE_NAMES = ["GBPEUR.csv", "GBPUSD.csv"]
DB = "validus.db"

def parse_row(row):
    if ";" in row:
        date, curr, val = str.split(row, ";")

        date = dt.datetime.strptime(date, '%d/%m/%Y')
        date = dt.datetime.strftime(date, '%Y-%m-%d')
        curr = curr.replace('"', '')
        if len(curr) == 6:
            trade_curr = curr[:3]
            base_curr = curr[3:]
            return date, trade_curr, base_curr, val
        else:
            raise ValueError("Incorrect Curreny Length")
    else:
        raise ValueError("Incorrect Delimiter")

def load_data():
    conn = sqlite3.connect(DB)
    crs = conn.cursor()

    def create_table():
        crs.execute("""
        CREATE TABLE IF NOT EXISTS m_fx_rate (
            value_date TEXT NOT NULL,
            trade_curr CHAR(3) NOT NULL,
            base_curr CHAR(3) NOT NULL,
            fx_rate DECIMAL(19, 9) NOT NULL,
            PRIMARY KEY (value_date, trade_curr, base_curr)
        )
        """)

    create_table()

    for f in FILE_NAMES:
        with open(f, 'r') as csvfile:
            reader = csv.reader(csvfile)
            # skip the header
            next(reader)
            data = [parse_row(x[0]) for x in reader]

            crs.executemany("""
            INSERT INTO m_fx_rate (value_date, trade_curr, base_curr, fx_rate)
            VALUES (?, ?, ?, ?)
            """, data)
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    load_data()