# 🧪 SDS & Chemical Stock Manager (QHSE)

Interactive web application built with **Python**, **Streamlit**, and **Pandas** to track chemical products, suppliers, expiration dates, and Safety Data Sheets (SDS / FDS), featuring flexible Excel/CSV import, manual entry, update history, and analytical charts.

---

## ✨ Key Features

- **Flexible Excel / CSV Import:** Automatic column matching even with varied header names (such as expiration date variants, quantity, supplier, CAS number, etc.).
- **Automated Status Alerts:** Real-time classification of items (`🔴 Expired`, `🟠 Expiring < 30d`, `🟡 Low stock`, `🟢 Compliant`).
- **Persistent Manual Entry:** Built-in form to add new products without overwriting session changes.
- **Search & Quick Filters:** Filter records by product name, CAS number, supplier, or status.
- **Direct SDS Access:** Clickable safety sheet links right inside the inventory table.
- **Pandas Analytics Charts:** Visual breakdowns of total quantities by category and supplier, plus item counts by status.
- **Update History:** Timestamped activity log in the left sidebar with support for custom follow-up notes.

---

## 🚀 Local Setup & Run

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/rchbob/gestionnaire-fds-stocks-qhse.git](https://github.com/rchbob/gestionnaire-fds-stocks-qhse.git)
   cd gestionnaire-fds-stocks-qhse
install
   pip install -r requirements.txt
running
   streamlit run app.py
