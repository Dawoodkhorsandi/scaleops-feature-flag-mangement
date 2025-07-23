# Feature Flag Management Service

A robust backend service for managing feature flags with dependency support and automatic audit logging, built with FastAPI and Clean Architecture principles.

This project demonstrates a highly decoupled and testable application structure by leveraging a dedicated dependency injection container, SQLAlchemy event listeners, and a layered architecture.

## ✨ Key Features

-   **Full CRUD Operations:** Create, read, and toggle feature flags.
-   **Dependency Management:** Define dependencies between feature flags. A flag can only be enabled if its dependencies are also enabled.
-   **Cascading Disables:** Disabling a parent flag automatically disables all flags that depend on it.
-   **Circular Dependency Detection:** The system prevents the creation of invalid dependency loops (e.g., Flag A -> Flag B -> Flag A).
-   **Automatic Audit Logging:** Every change to a feature flag is automatically recorded in an audit log, providing a complete history of operations.
-   **Clean Architecture:** The codebase is organized into distinct layers (Infrastructure, Repositories, Services, Routers) for high maintainability and testability.
-   **Modern Tooling:** Leverages modern Python features and libraries like `asyncio`, `Pydantic`, and `dependency-injector`.

## 🛠️ Tech Stack

-   **Framework:** FastAPI
-   **Database ORM:** SQLAlchemy 2.0 (with `asyncio` support)
-   **Data Validation:** Pydantic
-   **Dependency Injection:** `dependency-injector`
-   **Database:** PostgreSQL
-   **Code Formatting:** Black

## 🚀 Getting Started

Follow these steps to get the project up and running on your local machine.

### 1. Prerequisites

- Python 3.11+
- Poetry for dependency management.
- A running PostgreSQL database instance.

### 2. Installation

1.  Clone the repository:

    ```bash
    git clone <your-repository-url>
    cd scaleops-feature-flag-mangement
    ```

2.  Install dependencies using Poetry:

    ```bash
    poetry install
    ```

### 3. Environment Configuration

1.  The application requires a `.env` file to connect to the database. Create one by copying the example file:

    ```bash
    cp .env.example .env
    ```

2.  Open the newly created `.env` file and update the `DEPENDENCY_APP_POSTGRES_DSN` with your PostgreSQL connection string.

    ```properties
    # .env
    DEPENDENCY_APP_POSTGRES_DSN="postgresql+asyncpg://user:password@host:port/dbname"
    ```

### 4. Running the Application

Once the dependencies are installed and the `.env` file is configured, you can run the application using Uvicorn:

```bash
poetry run uvicorn src.app:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

### 5. API Documentation

FastAPI automatically generates interactive API documentation. Once the server is running, you can access it at:

-   Swagger UI: `http://127.0.0.1:8000/docs`
-   ReDoc: `http://127.0.0.1:8000/redoc`

## 💻 Development Workflow

To maintain a consistent code style and quality, this project uses pre-commit hooks.

### Pre-Commit Hooks with Black

We use Black, the uncompromising code formatter, to ensure all Python code follows a single, deterministic style.

1.  **Setup**

    After cloning the repository and installing dependencies, install the pre-commit hook into your local Git configuration:

    ```bash
    poetry run pre-commit install
    ```

    This command only needs to be run once per clone.

2.  **How It Works**

    Now, every time you run `git commit`, the following will happen automatically:

    1.  `pre-commit` will intercept the commit.
    2.  It will run `black` on all staged Python files.
    3.  If `black` makes no changes, your commit will proceed as normal.
    4.  If `black` reformats any of your files, it will abort the commit. This is expected behavior. Simply review the changes `black` made, add them to the staging area (`git add .`), and commit again. The second commit will succeed.

    This process ensures that no unformatted code ever makes it into the project's history.


## 🧪 Running Tests

This project uses `pytest` for its test suite.

### 1. Install Test Dependencies

Ensure you have the development dependencies installed, which includes `pytest`:

```bash
poetry install --with dev
```

### 2. Run Tests

You can run all tests from the project root directory:

```bash
poetry run pytest
```

