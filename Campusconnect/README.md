# CampusConnect Backend

Backend REST API for **CampusConnect**, a hackathon and campus opportunities platform built with **Python**, **Flask**, and **SQLite**.

---

## Project Structure

```text
Campusconnect/
├── app/
│   ├── __init__.py      # Application factory (create_app)
│   ├── config.py        # Environment loading & validation
│   ├── extensions.py    # SQLAlchemy & strict CORS setup
│   ├── errors.py        # Unified JSON error handlers
│   ├── cli.py           # Flask CLI management commands
│   ├── models/          # SQLite ORM models
│   ├── validators/      # Request parsing & input validation
│   ├── services/        # Business logic layer
│   ├── routes/          # Feature blueprints (/api/*)
│   └── utils/           # Response & auth helpers
├── tests/               # pytest test suite
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py
├── API_DOCS.md
└── README.md
```

---

## Setup & Run Instructions

### Windows PowerShell

```powershell
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env from template
Copy-Item .env.example .env

# 4. Generate a random SECRET_KEY (paste output into SECRET_KEY= in .env)
python -c "import secrets; print(secrets.token_urlsafe(48))"

# 5. Initialize the SQLite database
$env:FLASK_APP = "run.py"
flask init-db

# 6. Create an admin user (prompts securely for password, or pass --password)
flask create-admin --email admin@campusconnect.local

# Optional: seed sample admin, student, and opportunities for local development
flask seed-db

# 7. Run the server (reads HOST=0.0.0.0 and PORT=5000 from .env)
python run.py

# 8. Run tests
pytest -v
```

### macOS / Linux

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env from template
cp .env.example .env

# 4. Generate a random SECRET_KEY (paste output into SECRET_KEY= in .env)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# 5. Initialize the SQLite database
export FLASK_APP=run.py
flask init-db

# 6. Create an admin user (prompts securely for password, or pass --password)
flask create-admin --email admin@campusconnect.local

# 7. Run the server (reads HOST=0.0.0.0 and PORT=5000 from .env)
python3 run.py

# 8. Run tests
pytest -v
```

---

## Testing Endpoints with curl / PowerShell

### Windows PowerShell (`curl.exe` or `Invoke-RestMethod`)

```powershell
# Using curl.exe (note: in PowerShell, plain `curl` is an alias for Invoke-WebRequest)
curl.exe -s http://127.0.0.1:5000/api/health

# Using Invoke-RestMethod
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/health -Method Get
```

### macOS / Linux

```bash
curl -s http://127.0.0.1:5000/api/health
```

---

## LAN Setup & Teammate Access (Port 5000)

When your teammate is building the frontend on another computer on the same Wi-Fi/LAN:

1. **Find your LAN IP address**:
   - **Windows PowerShell**:
     ```powershell
     Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch "Loopback" -and $_.IPAddress -notmatch "^169\.254\." } | Select-Object InterfaceAlias, IPAddress
     ```
     (Or run `ipconfig` and look for `IPv4 Address` under your active Wi-Fi/Ethernet adapter, e.g., `192.168.1.15`.)
   - **macOS / Linux**:
     ```bash
     ifconfig | grep "inet "
     # or on Linux:
     hostname -I
     ```

2. **Add your teammate's frontend origin to `.env`**:
   ```env
   FRONTEND_ORIGINS=http://localhost:5173,http://192.168.1.20:5173
   ```
   *(Replace `192.168.1.20:5173` with your teammate's actual LAN IP and dev server port. Restart the backend after editing `.env`.)*

3. **Allow port `5000` through the firewall on Private networks**:
   - **Windows (Run PowerShell as Administrator)**:
     ```powershell
     New-NetFirewallRule -DisplayName "CampusConnect Flask 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -Profile Private
     ```
   - **macOS**: System Settings → Network → Firewall → allow incoming connections for Python if prompted.
   - **Ubuntu/Linux (UFW)**:
     ```bash
     sudo ufw allow from 192.168.0.0/16 to any port 5000 proto tcp
     ```

4. **Test from your teammate's computer** (replace `192.168.1.15` with your backend LAN IP):
   - Windows PowerShell: `curl.exe http://192.168.1.15:5000/api/health`
   - macOS / Linux: `curl http://192.168.1.15:5000/api/health`

---

## Frontend Developer Handoff

- **Base URL**: `http://<BACKEND_LAN_IP>:5000/api` (e.g., `http://192.168.1.15:5000/api`)
- **CORS**: Only origins listed in `FRONTEND_ORIGINS` are permitted. Allowed headers: `Authorization`, `Content-Type`.
- **Login Flow**:
  1. Register a student via `POST /api/auth/register` (or log in directly if already registered).
  2. Call `POST /api/auth/login` with `email` and `password` to receive a Bearer JWT (`access_token`) and `expires_in`.
  3. Store the token on the client and attach it to protected requests.
- **Authorization Header**:
  ```http
  Authorization: Bearer <access_token>
  ```
- **Standard Response & Error Format**:
  - Success:
    ```json
    {
      "success": true,
      "data": {}
    }
    ```
  - Error (`400`, `401`, `403`, `404`, `405`, `409`, `422`, `500`):
    ```json
    {
      "success": false,
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "Human-readable error message",
        "details": {}
      }
    }
    ```

See [API_DOCS.md](./API_DOCS.md) for full endpoint specifications.
