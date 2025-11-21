# NYU DevOps Project — Promotions Microservice

[![Build Status](https://github.com/CSCI-GA-2820-FA25-001/promotions/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-FA25-001/promotions/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/CSCI-GA-2820-FA25-001/promotions/branch/master/graph/badge.svg)](https://codecov.io/gh/CSCI-GA-2820-FA25-001/promotions)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Open in Remote - Containers](https://img.shields.io/badge/DevContainer-Open%20in%20VS%20Code-blue)](https://code.visualstudio.com/docs/devcontainers/containers)

---

## 📘 Overview
This repository implements the **Promotions Microservice** for an e-commerce platform as part of  
**NYU CSCI-GA 2820 – DevOps and Agile Methodologies (Homework 2: CI/CD and Kubernetes Deployment)**.

It demonstrates:
- **Test-Driven Development (TDD)**
- **Continuous Integration (CI)** with GitHub Actions
- **Automated coverage reporting** with Codecov
- **Containerized deployment** using Docker and VS Code Dev Containers
- **Web-based User Interface** for managing promotions

The service supports full **CRUD**, **search**, and **role-based listing** for product promotions,  
achieving **≥ 98 % coverage** (≥ 95 % required).

### 🌐 Web User Interface

A modern, responsive web interface is available for managing promotions through your browser.

**Access the UI:**
- Navigate to **[http://localhost:8080/ui](http://localhost:8080/ui)** after starting the service

**UI Features:**
- Create new promotions with form validation
- View all promotions in a sortable table
- Edit existing promotions inline
- Delete promotions with confirmation dialog
- Real-time discount price calculation display
- Status badges (draft, active, expired, deleted)
- Responsive design (mobile, tablet, desktop)
- Form validation and error handling
- Loading states and success messages

---

## 🧰 Development Environment (VS Code + Docker)

This project uses **VS Code Remote – Containers** and **Docker** to ensure a reproducible environment.

### Prerequisites
- Docker Desktop  
- Visual Studio Code  
- Remote – Containers extension  

### Setup Steps
```bash
git clone https://github.com/CSCI-GA-2820-FA25-001/promotions.git
cd promotions
code .
# When prompted, choose "Reopen in Container"
make build
make lint
make test
make run
````

Once running, the service will be available at **[http://localhost:8080](http://localhost:8080)** inside the container.

**Access the Web UI:**  
Navigate to **[http://localhost:8080/ui](http://localhost:8080/ui)** to manage promotions through the browser interface.

---

## 🚢 Container Image & Deployment Workflow

- The `Makefile` reads the image reference (`registry/image:tag`) directly from `k8s/deployment.yaml`, so `make build`, `make push`, and `make deploy` all stay in sync with the Kubernetes manifests.
- Default image: `cluster-registry:5000/promotions:1.0`. Override any part by exporting env vars, e.g. `make IMAGE_TAG=dev1 build push deploy`.
- `make cluster` provisions a local k3d cluster and registry that match the configured registry host/port (defaults to `cluster-registry:5000`).
- `make deploy` reapplies manifests and runs `kubectl set image deployment/promotions promotions=$IMAGE` to force the desired revision.
- Confirm the rollout with `kubectl get pods`; inspect logs via `kubectl logs deployment/promotions`.

Example end-to-end flow:

```bash
make cluster          # create k3d cluster + registry
make IMAGE_TAG=dev1 build
make IMAGE_TAG=dev1 push
make IMAGE_TAG=dev1 deploy
kubectl get pods
```

---

## 🧩 Continuous Integration and Coverage

Every Pull Request triggers GitHub Actions to run `flake8`, `pylint`, and `pytest`.
Coverage reports are uploaded to **Codecov**, with badges above showing build and coverage status.

✅ **Automatic CI/CD Pipeline**
✅ **Linting Standards (PEP 8 ≤ 127 chars)**
✅ **≥ 95 % Coverage Threshold (Actual 98 %)**
✅ **TDD Workflow validated via pytest + GitHub Actions**

---

## 🧮 Features

* 🧩 Complete CRUD + List Endpoints (`/promotions`, `/promotions/<id>`)
* 🌐 **Web User Interface** for browser-based promotion management
* 🧮 Automatic discounted price calculation (`amount` or `percent`)
* 🔐 Role-based views for Customer / Supplier / Manager
* 🕒 Expiration logic with state transitions (`draft → active → expired → deleted`)
* ⚙️ CLI Commands: `flask db-create`, `flask db-drop`
* 🧪 TDD & pytest suite (63 tests passed, 98 % coverage)

---

## ⚙️ Running Tests and Lint Checks

Run the unit tests and coverage report:

```bash
make test
```

Expected output:

```
TOTAL 352 statements, 8 missed → 98 %
63 tests passed ✅
```

Run lint checks:

```bash
make lint
```

Both `flake8` and `pylint` must pass with ≥ 9.5/10 rating as required by Professor Rofrano.

---

## 🧱 Data Model

| Field                            | Type                                       | Description                  |
| :------------------------------- | :----------------------------------------- | :--------------------------- |
| `id`                             | Integer (PK)                               | Auto-increment primary key   |
| `product_name`                   | String                                     | Unique product identifier    |
| `original_price`                 | Decimal(10, 2)                             | > 0 required                 |
| `discount_value`                 | Decimal(10, 2)                             | Optional (amount or percent) |
| `discount_type`                  | Enum(`amount`,`percent`)                   | Nullable                     |
| `promotion_type`                 | Enum(`discount`,`other`)                   | Required                     |
| `status`                         | Enum(`draft`,`active`,`expired`,`deleted`) | Default draft                |
| `start_date` / `expiration_date` | DateTime                                   | Expiration > Start           |
| `discounted_price`               | Computed property                          | Runtime only                 |

---

## 🔗 Key Endpoints

| Method | Endpoint                     | Description                         |
| :----- | :--------------------------- | :---------------------------------- |
| POST   | `/promotions`                | Create a new promotion              |
| GET    | `/promotions/<id>`           | Retrieve a promotion by ID          |
| PUT    | `/promotions/<id>`           | Update a promotion                  |
| DELETE | `/promotions/<id>`           | Soft delete promotion               |
| GET    | `/promotions`                | List/Search promotions (role-based) |
| POST   | `/promotions/<id>/duplicate` | Duplicate promotion (admin only)    |
| GET    | `/`                          | Service metadata                    |
| GET    | `/ui`                        | Web user interface                   |
| GET    | `/health`                    | Health check endpoint               |

---

## 🔐 Authentication & Authorization

This service uses an `X-Role` HTTP header for role-based access control.

**Available Roles:**

* `administrator` → Full CRUD access
* `customer` → Read only (active promotions)
* `supplier` → Read active + expired
* `manager` → Read all (promotions incl. deleted)

**Note:** The web UI (`/ui`) uses the `manager` role by default to display all promotions for management purposes.

Example request:

```bash
curl -X GET http://localhost:8080/promotions -H "X-Role: administrator"
```

---

## 🧠 Discount Calculation

```python
# Amount
original_price = 100.00; discount_value = 25.00
→ discounted_price = 75.00

# Percent
original_price = 100.00; discount_value = 20.0
→ discounted_price = 80.00
```

---

## 🧪 Coverage Summary

```
TOTAL 352 statements, 8 missed → 98 %
All 63 tests passed ✅
```

✅ Coverage ≥ 95 % (Actual 97.7 %)
✅ All tests green in CI pipeline
✅ Meets TDD and coverage rubric for full score

---

## 👩‍💻 Team Promotions (FA25)

**Jackie Wen**, **Yin (light12222)**, **Lokesh Boominathan**, **Sai Vishal**, **Daiveek S.**
**Instructor:** Prof. John J. Rofrano | **TA:** NYU DevOps Team

---

## 📜 License

Copyright (c) 2016–2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/).
Licensed under the [Apache 2.0 License](https://opensource.org/licenses/Apache-2.0).

This repository is part of the New York University (NYU) masters course:
**CSCI-GA 2820 DevOps and Agile Methodologies**, created and taught by [Prof. Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute and NYU Stern School of Business.
