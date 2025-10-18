import mysql.connector

class DatabaseManager:
    def __init__(self, host='localhost', user='root', password='', database='grocery_pos'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.conn.cursor(dictionary=True)
            print(" Connected to MySQL database.")
        except mysql.connector.Error as err:
            print(f" Database connection failed: {err}")

    def get_inventory(self):
        """Fetch all inventory items."""
        self.cursor.execute("SELECT * FROM inventory")
        return self.cursor.fetchall()

    def update_stock(self, item_id, new_stock):
        """Update stock of an item after purchase."""
        self.cursor.execute("UPDATE inventory SET stock = %s WHERE id = %s", (new_stock, item_id))
        self.conn.commit()

    def insert_transaction(self, timestamp, items_str, total, paid, change):
        """Save a completed transaction to the database."""
        self.cursor.execute(
            "INSERT INTO transactions (timestamp, items, total, paid, `change`) VALUES (%s, %s, %s, %s, %s)",
            (timestamp, items_str, total, paid, change)
        )
        self.conn.commit()

    def get_transactions(self):
        """Fetch all past transactions."""
        self.cursor.execute("SELECT * FROM transactions ORDER BY id DESC")
        return self.cursor.fetchall()

    def import_inventory(self, data):
        """Replace current inventory with imported JSON data."""
        self.cursor.execute("DELETE FROM inventory")
        for item in data:
            self.cursor.execute(
                "INSERT INTO inventory (name, price, stock) VALUES (%s, %s, %s)",
                (item['name'], item['price'], item['stock'])
            )
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
