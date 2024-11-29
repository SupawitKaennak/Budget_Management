import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import requests
import sqlite3

# ฟังก์ชันสำหรับดึงค่าเงินแบบเรียลไทม์
def fetch_exchange_rate(base_currency, target_currency):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            exchange_rate = data["rates"].get(target_currency)
            if exchange_rate:
                return exchange_rate
            else:
                messagebox.showerror("Error", f"ไม่รองรับการแปลงสกุลเงิน {target_currency}")
                return None
        else:
            messagebox.showerror("Error", "ไม่สามารถดึงข้อมูลอัตราแลกเปลี่ยนได้")
            return None
    except Exception as e:
        messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {e}")
        return None

# สร้างฐานข้อมูล
def setup_database():
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            amount REAL,
            type TEXT
        )
    """)
    conn.commit()
    conn.close()

# เพิ่มข้อมูลลงฐานข้อมูล
def add_transaction():
    date = date_entry.get()
    description = entry_description.get()
    amount = entry_amount.get()
    trans_type = combobox_type.get()

    if not date or not description or not amount or not trans_type:
        messagebox.showwarning("Warning", "กรุณากรอกข้อมูลให้ครบถ้วน")
        return

    try:
        amount = float(amount)
        conn = sqlite3.connect("budget.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (date, description, amount, type)
            VALUES (?, ?, ?, ?)
        """, (date, description, amount, trans_type))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "เพิ่มรายการสำเร็จ!")
        update_table()
    except ValueError:
        messagebox.showerror("Error", "กรุณากรอกจำนวนเงินเป็นตัวเลข")
    except Exception as e:
        messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {e}")

# แปลงเงินโดยเลือกสกุลเงิน
def convert_currency():
    try:
        base_currency = combobox_base_currency.get()
        target_currency = combobox_target_currency.get()
        amount = float(entry_foreign_amount.get())

        exchange_rate = fetch_exchange_rate(base_currency, target_currency)
        if exchange_rate is not None:
            converted_amount = amount * exchange_rate
            entry_amount.delete(0, tk.END)
            entry_amount.insert(0, f"{converted_amount:.2f}")
            messagebox.showinfo(
                "Success",
                f"{amount:.2f} {base_currency} เท่ากับ {converted_amount:.2f} {target_currency}\n"
                f"(อัตราแลกเปลี่ยน: {exchange_rate:.2f})"
            )
    except ValueError:
        messagebox.showerror("Error", "กรุณากรอกจำนวนเงินเป็นตัวเลข")
    except Exception as e:
        messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {e}")

# อัปเดตข้อมูลในตาราง
def update_table():
    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        tree.insert("", tk.END, values=row)

    update_balance()

# อัปเดตยอดเงินคงเหลือ
def update_balance():
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='รายรับ'")
    income = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='รายจ่าย'")
    expense = cursor.fetchone()[0] or 0
    conn.close()

    balance = income - expense
    label_balance.config(text=f"ยอดเงินคงเหลือ: {balance:.2f} บาท")

# ฟังก์ชันลบรายการ
def delete_transaction(event):
    try:
        selected_item = tree.selection()[0]  # เลือกรายการที่ถูกคลิก
        item_values = tree.item(selected_item, "values")
        transaction_id = item_values[0]  # ดึง ID ของรายการ

        # ยืนยันการลบ
        if messagebox.askyesno("ยืนยันการลบ", f"คุณต้องการลบรายการ ID: {transaction_id} หรือไม่?"):
            conn = sqlite3.connect("budget.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
            conn.commit()
            conn.close()

            tree.delete(selected_item)  # ลบจาก Treeview
            update_balance()  # อัปเดตยอดเงินคงเหลือ
            messagebox.showinfo("Success", "ลบรายการสำเร็จ!")
    except IndexError:
        messagebox.showerror("Error", "กรุณาเลือกหนึ่งรายการก่อนลบ")
    except Exception as e:
        messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {e}")



# สร้างหน้าต่างโปรแกรม
setup_database()
root = tk.Tk()
root.title("โปรแกรมจัดการงบประมาณส่วนตัว")
root.geometry("1280x720")

# สร้างเมนูคลิกขวา
popup_menu = tk.Menu(root, tearoff=0)
popup_menu.add_command(label="ลบรายการ", command=lambda: delete_transaction(None))

# ผูกเมนูคลิกขวากับ Treeview
def show_popup(event):
    try:
        tree.selection_set(tree.identify_row(event.y))  # เลือกรายการที่คลิก
        popup_menu.post(event.x_root, event.y_root)
    finally:
        popup_menu.grab_release()


# ช่องป้อนข้อมูล
frame_inputs = tk.Frame(root)
frame_inputs.pack(pady=10)

tk.Label(frame_inputs, text="วันที่ :").grid(row=0, column=0, padx=5)
date_entry = DateEntry(frame_inputs, date_pattern="yyyy-MM-dd")
date_entry.grid(row=0, column=1, padx=5)

tk.Label(frame_inputs, text="รายละเอียด :").grid(row=0, column=2, padx=5)
entry_description = tk.Entry(frame_inputs)
entry_description.grid(row=0, column=3, padx=5)

tk.Label(frame_inputs, text="จำนวนเงิน :").grid(row=0, column=4, padx=5)
entry_amount = tk.Entry(frame_inputs)
entry_amount.grid(row=0, column=5, padx=5)

tk.Label(frame_inputs, text="ประเภท :").grid(row=0, column=6, padx=5)
combobox_type = ttk.Combobox(frame_inputs, values=["รายรับ", "รายจ่าย"], state="readonly")
combobox_type.grid(row=0, column=7, padx=5)

btn_add = tk.Button(frame_inputs, text="เพิ่มรายการ", command=add_transaction)
btn_add.grid(row=0, column=8, padx=10)

# แปลงค่าเงิน
tk.Label(frame_inputs, text="สกุลเงินต้นทาง :").grid(row=1, column=0, padx=5)
combobox_base_currency = ttk.Combobox(frame_inputs, values=["USD", "CNY", "EUR", "JPY"], state="readonly")
combobox_base_currency.grid(row=1, column=1, padx=5)
combobox_base_currency.set("CNY")

tk.Label(frame_inputs, text="สกุลเงินปลายทาง :").grid(row=1, column=2, padx=5)
combobox_target_currency = ttk.Combobox(frame_inputs, values=["THB", "USD", "CNY", "EUR", "JPY"], state="readonly")
combobox_target_currency.grid(row=1, column=3, padx=5)
combobox_target_currency.set("THB")

tk.Label(frame_inputs, text="จำนวนเงินต้นทาง :").grid(row=1, column=4, padx=5)
entry_foreign_amount = tk.Entry(frame_inputs)
entry_foreign_amount.grid(row=1, column=5, padx=5)

btn_convert = tk.Button(frame_inputs, text="แปลงค่าเงิน", command=convert_currency)
btn_convert.grid(row=1, column=6, padx=5)

# ตาราง
tree = ttk.Treeview(root, columns=("ID", "Date", "Description", "Amount", "Type"), show="headings", height=15)
tree.pack(pady=10)
tree.bind("<Button-3>", show_popup)  # คลิกขวา
tree.heading("ID", text="ID")
tree.heading("Date", text="วันที่")
tree.heading("Description", text="รายละเอียด")
tree.heading("Amount", text="จำนวนเงิน")
tree.heading("Type", text="ประเภท")

# ยอดเงินคงเหลือ
label_balance = tk.Label(root, text="ยอดเงินคงเหลือ : 0.00 บาท", font=("Arial", 14))
label_balance.pack(pady=10)

# เริ่มโปรแกรม
update_table()
root.mainloop()
