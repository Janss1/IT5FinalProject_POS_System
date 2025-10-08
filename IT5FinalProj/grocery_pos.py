import sys
import os
import json
import csv
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QListWidget, QPushButton,
    QLabel, QSpinBox, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QMessageBox, QLineEdit, QGroupBox, QFormLayout, QFileDialog, QTextEdit
)
from PyQt5.QtCore import Qt

INVENTORY_FILE = 'inventory.json'
TRANSACTIONS_FILE = 'transactions.csv'
RECEIPTS_FOLDER = 'receipts'

SAMPLE_INVENTORY = [
    {"id": 1, "name": "Rice (5kg)", "price": 250.00, "stock": 20},
    {"id": 2, "name": "Cooking Oil (1L)", "price": 120.00, "stock": 15},
    {"id": 3, "name": "Sugar (1kg)", "price": 60.00, "stock": 30},
    {"id": 4, "name": "Salt (1kg)", "price": 20.00, "stock": 40},
    {"id": 5, "name": "Instant Noodles", "price": 15.00, "stock": 100},
]


def ensure_files():
    if not os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(SAMPLE_INVENTORY, f, indent=2)

    if not os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'items', 'total', 'paid', 'change'])

    if not os.path.exists(RECEIPTS_FOLDER):
        os.makedirs(RECEIPTS_FOLDER)


class Inventory:
    def __init__(self, filename=INVENTORY_FILE):
        self.filename = filename
        self.load()

    def load(self):
        with open(self.filename, 'r', encoding='utf-8') as f:
            self.items = json.load(f)

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, indent=2)

    def find_by_name(self, name):
        for item in self.items:
            if item['name'] == name:
                return item
        return None

    def reduce_stock(self, item_id, qty):
        for item in self.items:
            if item['id'] == item_id:
                if item['stock'] >= qty:
                    item['stock'] -= qty
                    self.save()
                    return True
                else:
                    return False
        return False


class POSMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Grocery POS System')
        self.inventory = Inventory()
        self.cart = []
        self.init_ui()

    def init_ui(self):
        main = QWidget()
        main_layout = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(QLabel('<b>Inventory</b>'))
        self.inv_list = QListWidget()
        self.refresh_inventory_list()
        left.addWidget(self.inv_list)

        controls = QHBoxLayout()
        self.qty_spin = QSpinBox(); self.qty_spin.setMinimum(1); self.qty_spin.setMaximum(999)
        controls.addWidget(QLabel('Qty:'))
        controls.addWidget(self.qty_spin)
        add_btn = QPushButton('Add to Cart')
        add_btn.clicked.connect(self.add_to_cart)
        controls.addWidget(add_btn)
        left.addLayout(controls)

        view_inv_btn = QPushButton('Refresh Inventory')
        view_inv_btn.clicked.connect(self.refresh_inventory_list)
        import_btn = QPushButton('Import Inventory...')
        import_btn.clicked.connect(self.import_inventory)
        left.addWidget(view_inv_btn)
        left.addWidget(import_btn)

        main_layout.addLayout(left, 2)

        right = QVBoxLayout()
        right.addWidget(QLabel('<b>Cart</b>'))
        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels(['Name', 'Price', 'Qty', 'Subtotal'])
        right.addWidget(self.cart_table)

        cart_buttons = QHBoxLayout()
        remove_btn = QPushButton('Remove Selected')
        remove_btn.clicked.connect(self.remove_selected_cart)
        cart_buttons.addWidget(remove_btn)
        clear_btn = QPushButton('Clear Cart')
        clear_btn.clicked.connect(self.clear_cart)
        cart_buttons.addWidget(clear_btn)
        right.addLayout(cart_buttons)

        checkout_group = QGroupBox('Checkout')
        form = QFormLayout()
        self.total_label = QLabel('0.00')
        form.addRow('Total:', self.total_label)
        self.paid_input = QLineEdit()
        self.paid_input.setPlaceholderText('Enter cash paid')
        form.addRow('Paid:', self.paid_input)
        checkout_btn = QPushButton('Complete Transaction')
        checkout_btn.clicked.connect(self.complete_transaction)
        form.addRow(checkout_btn)
        checkout_group.setLayout(form)
        right.addWidget(checkout_group)

        history_btn = QPushButton('View Transaction History')
        history_btn.clicked.connect(self.view_history)
        right.addWidget(history_btn)

        main_layout.addLayout(right, 3)

        main.setLayout(main_layout)
        self.setCentralWidget(main)
        self.resize(900, 500)

    def refresh_inventory_list(self):
        self.inventory.load()
        self.inv_list.clear()
        for item in self.inventory.items:
            text = f"{item['name']} — ₱{item['price']:.2f} (stock: {item['stock']})"
            self.inv_list.addItem(text)

    def get_selected_inventory_item(self):
        sel = self.inv_list.currentItem()
        if not sel:
            return None
        name = sel.text().split(' — ')[0]
        return self.inventory.find_by_name(name)

    def add_to_cart(self):
        inv_item = self.get_selected_inventory_item()
        if not inv_item:
            QMessageBox.warning(self, 'No selection', 'Please select an item.')
            return
        qty = int(self.qty_spin.value())
        if inv_item['stock'] < qty:
            QMessageBox.warning(self, 'Insufficient stock', f"Only {inv_item['stock']} left.")
            return
        for c in self.cart:
            if c['id'] == inv_item['id']:
                if inv_item['stock'] < c['qty'] + qty:
                    QMessageBox.warning(self, 'Insufficient stock', f"Only {inv_item['stock']} left.")
                    return
                c['qty'] += qty
                self.refresh_cart_table()
                return
        self.cart.append({'id': inv_item['id'], 'name': inv_item['name'], 'price': inv_item['price'], 'qty': qty})
        self.refresh_cart_table()

    def refresh_cart_table(self):
        self.cart_table.setRowCount(0)
        total = 0.0
        for item in self.cart:
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)
            self.cart_table.setItem(row, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(row, 1, QTableWidgetItem(f"{item['price']:.2f}"))
            self.cart_table.setItem(row, 2, QTableWidgetItem(str(item['qty'])))
            subtotal = item['price'] * item['qty']
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"{subtotal:.2f}"))
            total += subtotal
        self.total_label.setText(f"₱{total:.2f}")

    def remove_selected_cart(self):
        row = self.cart_table.currentRow()
        if row < 0:
            return
        del self.cart[row]
        self.refresh_cart_table()

    def clear_cart(self):
        self.cart = []
        self.refresh_cart_table()

    def complete_transaction(self):
        if not self.cart:
            QMessageBox.warning(self, 'Empty cart', 'Cart is empty.')
            return
        try:
            paid = float(self.paid_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, 'Invalid input', 'Enter valid payment amount.')
            return

        total = sum(item['price'] * item['qty'] for item in self.cart)
        if paid < total:
            QMessageBox.warning(self, 'Insufficient payment', 'Paid amount is less than total.')
            return

        change = paid - total

        for item in self.cart:
            ok = self.inventory.reduce_stock(item['id'], item['qty'])
            if not ok:
                QMessageBox.critical(self, 'Stock error', f"Not enough stock for {item['name']}")
                return

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        items_str = ';'.join([f"{c['name']}x{c['qty']}@{c['price']:.2f}" for c in self.cart])
        with open(TRANSACTIONS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, items_str, f"{total:.2f}", f"{paid:.2f}", f"{change:.2f}"])

        receipt_text = self.generate_receipt_text(timestamp, total, paid, change)
        self.show_receipt(receipt_text)

        QMessageBox.information(self, 'Transaction Complete', f"Total: ₱{total:.2f}\nPaid: ₱{paid:.2f}\nChange: ₱{change:.2f}")
        self.cart = []
        self.paid_input.clear()
        self.refresh_cart_table()
        self.refresh_inventory_list()

    def generate_receipt_text(self, timestamp, total, paid, change):
        filename = os.path.join(RECEIPTS_FOLDER, f"receipt_{timestamp}.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('----------------------------------------\n')
            f.write('   FreshMart Grocery POS\n')
            f.write('----------------------------------------\n')
            f.write(f"Date: {timestamp}\n")
            f.write('Cashier: Default\n')
            f.write('----------------------------------------\n')
            f.write('Item                     Qty   Subtotal\n')
            f.write('----------------------------------------\n')
            for item in self.cart:
                name = item['name'][:22].ljust(22)
                qty = str(item['qty']).rjust(3)
                subtotal = f"₱{item['price'] * item['qty']:.2f}".rjust(9)
                f.write(f"{name}{qty}{subtotal}\n")
            f.write('----------------------------------------\n')
            f.write(f"TOTAL: {str('₱'+format(total, '.2f')).rjust(28)}\n")
            f.write(f"CASH: {str('₱'+format(paid, '.2f')).rjust(29)}\n")
            f.write(f"CHANGE: {str('₱'+format(change, '.2f')).rjust(27)}\n")
            f.write('----------------------------------------\n')
            f.write('Thank you for shopping with us!\n')
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()

    def show_receipt(self, receipt_text):
        dlg = QWidget()
        dlg.setWindowTitle('Receipt')
        layout = QVBoxLayout()
        text_box = QTextEdit()
        text_box.setPlainText(receipt_text)
        text_box.setReadOnly(True)
        layout.addWidget(text_box)
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn)
        dlg.setLayout(layout)
        dlg.resize(400, 500)
        dlg.show()
        self.receipt_dialog = dlg

    def view_history(self):
        if not os.path.exists(TRANSACTIONS_FILE):
            QMessageBox.information(self, 'No transactions', 'No transaction history found.')
            return
        dlg = QWidget()
        dlg.setWindowTitle('Transaction History')
        layout = QVBoxLayout()
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(['Timestamp', 'Items', 'Total', 'Paid', 'Change'])
        with open(TRANSACTIONS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                r = table.rowCount()
                table.insertRow(r)
                for i, val in enumerate(row):
                    table.setItem(r, i, QTableWidgetItem(val))
        layout.addWidget(table)
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn)
        dlg.setLayout(layout)
        dlg.resize(800, 400)
        dlg.show()
        self.history_dialog = dlg

    def import_inventory(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Import inventory JSON', '', 'JSON Files (*.json);;All Files (*)')
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError('Inventory must be a list of items')
            self.inventory.items = data
            self.inventory.save()
            self.refresh_inventory_list()
            QMessageBox.information(self, 'Imported', 'Inventory imported successfully.')
        except Exception as e:
            QMessageBox.critical(self, 'Import failed', str(e))


if __name__ == '__main__':
    ensure_files()
    app = QApplication(sys.argv)
    window = POSMainWindow()
    window.show()
    sys.exit(app.exec_())
