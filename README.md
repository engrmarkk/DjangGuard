# DjangGuard

A security-focused Django REST API boilerplate with built-in authentication, rate limiting, JWT token management, and Redis-backed caching. Designed to serve as a hardened starting point for building production-ready APIs.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Running the Server](#running-the-server)
- [API Reference](#api-reference)
  - [Authentication](#authentication)
  - [Users](#users)
- [Security Architecture](#security-architecture)
- [Rate Limiting](#rate-limiting)
- [Middleware](#middleware)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

DjangGuard is a batteries-included Django REST Framework (DRF) backend template built with security at its core. It combines JWT-based authentication, brute-force protection, user-agent binding, Redis-backed token blacklisting, and global rate limiting — all wired together and ready to extend.

---

## Features

- **JWT Authentication** via `djangorestframework-simplejwt` with custom claims (user agent binding)
- **Token Blacklisting** using Redis — tokens are invalidated on logout and revoked on device mismatch
- **Brute-Force Protection** via `django-axes` — accounts are locked after 5 failed login attempts (1-hour cooldown)
- **Global Rate Limiting** — 100 requests/hour per IP (unauthenticated) or per user ID (authenticated)
- **Endpoint-Level Rate Limiting** — login and register endpoints are limited to 5 requests/minute per email and 10 requests/minute per IP
- **User Agent Validation Middleware** — tokens are bound to the device/browser that issued them; mismatched requests are rejected and tokens are blacklisted automatically
- **Argon2 Password Hashing** — uses the strongest available password hasher by default
- **Strong Password Validation** — minimum 12 characters with similarity, common-password, and numeric-only checks
- **Redis Caching** — user profile data is cached for 1 hour to reduce database load
- **Custom Exception Handling** — consistent JSON error responses across all DRF exceptions and rate limit violations
- **Custom 404 & 500 Handlers** — structured JSON error responses for non-DRF errors
- **Email-Based Authentication** — username field removed; email is the unique identifier
- **Hex UUID Primary Keys** — all models use non-sequential, hex-based UUIDs as primary keys

---

## Tech Stack

| Layer              | Technology                          |
|--------------------|--------------------------------------|
| Framework          | Django 5.2, Django REST Framework    |
| Authentication     | SimpleJWT, PyJWT                    |
| Brute-Force Guard  | django-axes                         |
| Rate Limiting      | django-ratelimit                    |
| Caching / Sessions | Redis                               |
| Password Hashing   | Argon2 (via argon2-cffi)            |
| Environment Config | python-dotenv                       |
| Database (default) | SQLite (swap for PostgreSQL in prod)|

---

## Project Structure

```
DjangGuard/
└── backend/
    ├── api_services/
    │   ├── const_response/     # Standardized API response helper
    │   ├── custom_exceptions/  # Custom 404/500 view handlers
    │   ├── dbCruds/            # Reusable database operation helpers
    │   ├── environmentals/     # Environment variable loader
    │   ├── logger/             # Centralized logger setup
    │   ├── redis_service/      # Redis client wrapper
    │   └── utils/              # JWT token generation, UUID, misc helpers
    ├── authentication/
    │   ├── models.py           # Custom User model, UserLoginRecord
    │   ├── serializers.py      # Login and Register serializers
    │   ├── views.py            # LoginView, RegisterView, LogoutView
    │   └── urls.py             # /api/auth/* routes
    ├── exception_handler/      # Custom DRF exception handler
    ├── guard/
    │   ├── settings.py         # Django settings
    │   └── urls.py             # Root URL configuration
    ├── middleWares/
    │   ├── authenticate/       # UserAgentValidationMiddleware
    │   └── rateLimit/          # GlobalRateLimitMiddleware
    ├── users/
    │   ├── views.py            # UserProfileView
    │   └── urls.py             # /api/users/* routes
    ├── manage.py
    └── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Redis server running locally or via a remote URL
- `pip` for package installation

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/your-username/DjangGuard.git
cd DjangGuard/backend
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables** (see [Environment Variables](#environment-variables))

**5. Apply database migrations**

```bash
python manage.py migrate
```

### Environment Variables

Create a `.env` file in the `backend/` directory with the following keys:

```env
SECRET_KEY=your-django-secret-key

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
CACHE_REDIS_URL=redis://127.0.0.1:6379/0
```

> **Note:** Never commit your `.env` file. It is already listed in `.gitignore`.

### Running the Server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

---

## API Reference

All endpoints return a consistent JSON structure:

```json
{
  "status": "success | failed",
  "message": "Human-readable message",
  "data": { }
}
```

### Authentication

Base path: `/api/auth/`

#### `POST /api/auth/register`

Register a new user account.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "first_name": "Jane",
  "last_name": "Doe"
}
```

**Response:** `201 Created`

```json
{
  "status": "success",
  "message": "User registered successfully"
}
```

**Rate Limit:** 5 requests/minute per email · 10 requests/minute per IP

---

#### `POST /api/auth/login`

Authenticate with email and password. Returns a JWT access token.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}
```

**Response:** `200 OK`

```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "access": "<jwt_access_token>"
  }
}
```

**Rate Limit:** 5 requests/minute per email · 10 requests/minute per IP  
**Brute-Force Lock:** Account locks after 5 failed attempts for 1 hour

---

#### `POST /api/auth/logout`

Invalidate the current JWT token by blacklisting its `jti` in Redis.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

```json
{
  "status": "success",
  "message": "Logout successful"
}
```

---

### Users

Base path: `/api/users/`

#### `GET /api/users/me`

Retrieve the authenticated user's profile. Response is cached in Redis for 1 hour.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

```json
{
  "status": "success",
  "message": "User profile retrieved successfully",
  "data": {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "user@example.com",
    "date_joined": "2025-01-01T00:00:00Z"
  }
}
```

**Rate Limit:** 4 requests/minute per authenticated user

---

## Security Architecture

DjangGuard layers multiple security mechanisms that work together:

### JWT + User Agent Binding

When a user logs in, the `User-Agent` header is embedded as a custom claim inside the JWT. On every subsequent request, the `UserAgentValidationMiddleware` compares the token's `user_agent` claim against the incoming request's `User-Agent`. If they differ (indicating a stolen token being used on a different device), the token is immediately blacklisted in Redis and the request is rejected.

### Redis Token Blacklist

On logout, the token's `jti` (JWT ID) is written to Redis with a TTL matching the token's remaining lifetime. Every authenticated request checks Redis for the `jti` before proceeding. If the `jti` is found and marked `"blacklisted"`, the request is denied — even if the token's signature is otherwise valid.

### Single Active Session

When a user logs in, their `user_id` is mapped to their current token's `jti` in Redis. If the user logs in from a new session, any request using the old `jti` is rejected as a revoked token, effectively enforcing single active session behavior.

### Argon2 Password Hashing

Passwords are hashed using Argon2id by default — the winner of the Password Hashing Competition and recommended by OWASP. PBKDF2 is kept as a fallback.

### Brute-Force Protection (django-axes)

Failed login attempts are tracked per IP. After 5 failures, the account is locked out for 1 hour. Successful login resets the failure counter (`AXES_RESET_ON_SUCCESS = True`).

---

## Rate Limiting

| Scope               | Limit             | Applied To                         |
|---------------------|-------------------|------------------------------------|
| Global (anonymous)  | 100 requests/hour | Per IP address                     |
| Global (auth)       | 100 requests/hour | Per user ID                        |
| Login endpoint      | 5/min + 10/min    | Per email field + Per IP           |
| Register endpoint   | 5/min + 10/min    | Per email field + Per IP           |
| User profile (GET)  | 4 requests/minute | Per authenticated user             |

Rate limit violations return HTTP `429 Too Many Requests` with a `Retry-After` header.

---

## Middleware

Middleware is applied in the following order (relevant custom layers):

1. **`AxesMiddleware`** — Tracks and enforces login attempt lockouts
2. **`GlobalRateLimitMiddleware`** — Enforces global per-IP / per-user request limits and appends `X-RateLimit-*` headers to responses
3. **`UserAgentValidationMiddleware`** — Validates JWT user agent binding, checks Redis blacklist, and enforces single active session logic on every authenticated request

---

## Contributing

Contributions are welcome! To get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "feat: describe your change"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

Please ensure your code follows existing conventions and includes appropriate tests.

---

[//]: # (## License)

[//]: # (This project is open source. Add your preferred license here &#40;e.g., MIT, Apache 2.0&#41;.)