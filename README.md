# Project-Express

A lightweight, production-ready monolithic sandbox application built with **Node.js**, **Express.js**, and **SQLite** (via `sql.js`). This application serves as a functional test environment for validating and benchmarking the "AI Sprint Intelligence" automation program.

---

## Features

- **Home Page** — Welcoming landing page with navigation to all areas.
- **Dashboard** — High-level summary view showing total item counts and recent additions.
- **Item Management** — Full CRUD interface: create, read, update, and delete records.
- **SQLite Database** — Auto-initialized on first run with sample seed data (3 records).
- **Clean UI** — Semantic, responsive design with a polished interface.

## Quick Start

### 1. Install dependencies

```bash
npm install
```

### 2. Start the server

```bash
npm start
```

The server will start on **http://localhost:3000**.

### 3. Open in your browser

| Page        | URL                          |
|-------------|------------------------------|
| Home        | http://localhost:3000/       |
| Dashboard   | http://localhost:3000/dashboard |
| Manage Items| http://localhost:3000/items  |

---

## Project Structure

```
.
├── app.js                # Express application entry point
├── database.js           # SQLite initialization & seed logic
├── database.sqlite       # SQLite database file (auto-generated)
├── package.json          # Project manifest & dependencies
├── README.md             # This file
├── routes/
│   └── items.js          # CRUD route handlers
├── views/
│   ├── index.ejs         # Home page
│   ├── dashboard.ejs     # Dashboard page
│   └── items.ejs         # Item management page
└── public/
    └── css/
        └── style.css     # Application styles
```

## API Endpoints

| Method | Path                     | Description          |
|--------|--------------------------|----------------------|
| GET    | `/`                      | Home page            |
| GET    | `/dashboard`             | Dashboard summary    |
| GET    | `/items`                 | List all items       |
| POST   | `/items`                 | Create a new item    |
| POST   | `/items/:id/update`      | Update an item       |
| POST   | `/items/:id/delete`      | Delete an item       |

## Tech Stack

- **Runtime:** Node.js
- **Framework:** Express.js 4.x
- **Database:** SQLite (via `sql.js`)
- **Templating:** EJS
- **Styling:** Plain CSS
