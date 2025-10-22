# **FleetWise - Vehicle Fleet Management System**

> **ENPM680 Fall 2025** | Vivek Chaurasia | vivekc03@umd.edu

A web-based fleet management system with role-based access for Fleet Managers and Fleet Users.

---

## 🛠️ **Tech Stack**

- **Backend:** FastAPI + MySQL + SQLAlchemy (async)
- **Frontend:** React + Vite + TailwindCSS
- **Auth:** JWT with bcrypt

---

## 📦 **Prerequisites**

- Python 3.11+
- Node.js 18+
- MySQL 8.0+

---

## 🚀 **Quick Setup**

### **1. Clone Repository**

```bash
git clone https://github.com/yourusername/enpm680fall25project-vivekc03.git
cd enpm680fall25project-vivekc03
```

---

### **2. Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your MySQL credentials
```

**`.env` Configuration:**
```env
DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/fleetwise
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=fleetwise

SECRET_KEY=81b7dd93097b9fde73815d040badf018ba41c0c721009db8643f3cb276ccf5e3
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

APP_NAME=FleetWise
DEBUG=True
CORS_ORIGINS=http://localhost:5173
```

**Create Database & Run Migrations:**
```bash
# Create database
mysql -u root -p
CREATE DATABASE fleetwise;
EXIT;

# Run migrations
# Before you run the below command make sure you have set the password for mysql db correctly.
alembic upgrade head 

# Seed test data
python scripts/seed_db.py
```

**Start Backend:**
```bash
python run.py
```

Backend runs at: **http://localhost:8000**

---

### **3. Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Start frontend
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## 👥 **Test Credentials**

### **Fleet Managers:**
- **Email:** manager1@fleetwise.com | **Password:** Manager@123
- **Email:** manager2@fleetwise.com | **Password:** Manager@456

### **Fleet Users:**
Register at `/register` or use:
- **Email:** john@example.com | **Password:** Password@123

---

## 📡 **API Documentation**

Visit **http://localhost:8000/docs** for interactive Swagger UI


## 📞 **Contact**

**Vivek Chaurasia** | vivekc03@umd.edu | ENPM680 Fall 2025 | +1 (240) 4130-6570
