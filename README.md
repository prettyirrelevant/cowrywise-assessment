# 📚 Cowrywise Assessment

[![CI Status](https://github.com/prettyirrelevant/cowrywise-assessment/workflows/CI/badge.svg)](https://github.com/prettyirrelevant/cowrywise-assessment/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This project is a submission for the Backend Engineer (Infrastructure, API Engineer, DevOps) role at Cowrywise.

## 🏗️ Architecture

Our system comprises four main services:

1. **Librarian** (Admin API): Manages the library catalog and user data.
2. **Bookworm** (Frontend API): Handles user interactions and book borrowing.
3. **Pagekeeper** (Authentication): Ensures secure access to our services (internal only).
4. **Bookcourier** (Message Transport): Facilitates inter-service communication.

![](./arch_diagram.png?raw=true)

## 🚀 Quick Start

### Local Setup

> [!NOTE]
> This guide assumes you have [uv](https://github.com/astral-sh/uv) installed.

1. Clone and navigate to the repository:
   ```bash
   git clone https://github.com/prettyirrelevant/cowrywise-assessment.git
   cd cowrywise-assessment
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Configure environment:
   ```bash
   cp .env.example .env.local
   ```

4. Start services:
   ```bash
   make pagekeeper-dev
   make bookworm-dev
   make librarian-dev
   ```

### Docker Setup

1. Ensure Docker and Docker Compose are installed.

2. Configure environment:
   ```bash
   cp .env.example .env
   ```

3. Build and start services:
   ```bash
   docker-compose up --build
   ```

## 📚 API Documentation

- Pagekeeper (Authentication): Internal gRPC service.
- Librarian (Admin API): [http://localhost:8084/docs](http://localhost:8084/docs)
- Bookworm (Frontend API): [http://localhost:8080/docs](http://localhost:8080/docs)

## 🧪 Testing

Run the test suite:

```bash
make test-librarian && make test-pagekeeper  && make test-bookworm
```

## 🚢 Deployment

The project uses Docker for containerization. Key points:

- Librarian and Bookworm are exposed externally.
- Pagekeeper is an internal service, not exposed outside the Docker network.
- RabbitMQ is used for inter-service communication.
- MongoDB and PostgreSQL are used for data storage.

Refer to `docker-compose.yml` and Dockerfiles in `infra/` for detailed configuration.

## 🔐 Authentication

Pagekeeper provides gRPC endpoints for user management:

- Register
- Authenticate
- Verify
- FetchUsers

For detailed proto definitions, see the `pagekeeper.proto` file.

## 🔧 Environment Variables

Key variables for each service are defined in `.env.example`. Ensure to set appropriate values for your environment as the default provided is for Docker.
