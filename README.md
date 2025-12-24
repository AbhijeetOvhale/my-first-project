## Online Snacks Center Mini Project with help of ChatGPT..

A full-stack online snacks center system built with Django with the help of ChatGPT. This application allows customers to order snacks and track their status in real-time, while providing the business owner with a comprehensive dashboard to manage inventory, orders, and sales reports.

## 🚀 Features

### 👤 Customer Panel
* Menu Browsing: View diverse snacks with images and prices (Vada Pav, Misal Pav, etc.).
* Cart Management: Add items, update quantities, and review the total bill.
* Secure Checkout: Choose between Cash or Cashless payment modes.
* Live Order Tracking: Real-time updates (Preparing → Ready) using AJAX polling without refreshing the page.
* Order History: View past orders and payment status.

### 👨‍🍳 Owner Dashboard (Admin)
* Live Order Management: View incoming orders and update their status (Pending → Preparing → Completed).
* Inventory Control: Add, update, or delete snacks and manage stock availability.
* Sales Reports: Visual graphs (using Chart.js) to track daily revenue and popular items.
* Feedback System: View ratings and reviews from customers.

## 🛠 Tech Stack

* Backend: Python, Django
* Frontend: HTML5, CSS3, Bootstrap 5
* Scripting: JavaScript (AJAX for live status updates)
* Visualization: Chart.js (for analytics)
* Database: SQLite (Default)

## ⚙️ Installation & Setup

Follow these steps to run the project locally:

1.  Clone the repository:
   
    git clone [https://github.com/AbhijeetOvhale/my-first-project](https://github.com/AbhijeetOvhale/my-first-project)

    cd my-first-project
    
3.  Create and activate a virtual environment:
   
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    
4.  Install dependencies:
   
    pip install -r requirements.txt
    
5.  Apply database migrations:
   
    python manage.py migrate
    
6.  Run the server:
   
    python manage.py runserver
    
7.  Open the app:
    Visit http://127.0.0.1:8000/ in your browser.

(You can also find all the important ready to paste codes, in the 'osc project all codes' file!)

## 🔑 Login Credentials

To test the Owner Dashboard, use the following credentials:
* Email: owner@gmail.com
* Password: owner123

*(Note: Customers can register a new account on the signup page.)*

## 📸 Screenshots
screenshots are in running_demo folder.
