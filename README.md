# BlogBlaze - A Production-Grade Blog Platform

A modern, feature-rich blogging platform built with a robust, modular architecture designed following production-grade best practices. BlogBlaze demonstrates enterprise-level software engineering principles with complete separation of concerns, reusable components, and database-agnostic design.

## 🎯 Project Overview

BlogBlaze is a comprehensive blog management system where users can:
- **Create & Publish** blog posts
- **Discover & Read** posts from other users
- **Rate & Review** posts with feedback
- **Manage Accounts** with secure authentication
- **Email verification** and **Reset Passwords** through secure token based link. 

The application serves as a showcase of professional backend architecture suitable for production environments, featuring industry-standard practices and patterns.


## 🏗️ Architecture & Design Principles

### Modular Architecture

BlogBlaze implements a highly organized modular structure that adheres to **Single Responsibility Principle (SRP)** and **Separation of Concerns (SoC)**. This design ensures:

- **Reusability**: Modules can be independently used in other projects
- **Maintainability**: Clear separation makes code easier to understand and modify
- **Scalability**: New features can be added without affecting existing components
- **Testability**: Each module can be tested in isolation

### Project Structure

```
BlogBlaze/
├── routers/                    # API and page routing
│   ├── api/                   # REST API endpoints
│   │   ├── posts.py          # Post management endpoints
│   │   └── users.py          # User management endpoints
│   └── pages/                # Page rendering routes
│       ├── posts_pages.py    # Post display pages
│       ├── users_pages.py    # User pages
│       └── account_access.py # Authentication pages
├── data_services/             # Business Logic Layer
│   ├── posts_service.py      # Post operations logic
│   └── users_service.py      # User operations logic
├── models.py                  # Database models (SQLAlchemy ORM)
├── schemas.py                # Request/Response data validation (Pydantic)
├── database.py               # Database connection & session management
├── auth.py                   # password hashing and authorization logic
├── access_manager.py         # Authorization & access control logic
├── logging_config/            # Logging infrastructure
│   ├── log_manager.py       # Logging configuration manager
│   └── log_config.py        # Logging settings
├── utils/                     # Utility modules
│   ├── email_manager.py     # Email operation orchestration
│   ├── email_sender_smtp.py # SMTP email delivery
│   ├── image_utils.py       # Image processing utilities
│   └── html_utils.py        # HTML processing utilities
├── sysdata/
│   └── email_templates/      # Email template files
├── templates/                 # HTML templates for frontend
├── static/                    # Static assets (CSS, JS, images)
├── media/                     # User-uploaded media files
├── main.py                   # Application entry point
└── requirements.txt          # Python dependencies
```

## 🔑 Core Features

### 1. **User Authentication & Security**

#### Complete Authentication System
- **User Registration**: Secure account creation with validation
- **Email Verification**: Account activation through email verification link 
- **Login System**: Secure credentials verification for login
- **Password Reset**: Forgot password flow through registered email 
- **JWT Token Authentication**: Industry-standard token-based authentication
- **Protected Routes**: Dependency injection for route protection

### 2. **Authorization & Access Control**
- Core authentication logic independent of frameworks
- **Access Manager Module**: Centralized authorization logic
- **Protected Endpoints**: Automatic user verification via dependency functions

**File**: `access_manager.py` - Reusable authorization module

### 3. **Business Logic Separation**

The application strictly separates business logic from request handlers:

```
Request Handler (routers/) 
    ↓
Service Layer (data_services/)
    ↓
Database Access (models.py via SQLAlchemy)
```

**Benefits**:
- Business logic is **UI-agnostic** and can be reused in other applications
- Easy to test and mock dependencies
- Simple to extend with new features without touching existing code

**Files**:
- `data_services/posts_service.py` - Post operations
- `data_services/users_service.py` - User operations

### 4. **Modular Email Management**

Completely independent email module with:
- **Email Manager** (`email_manager.py`): High-level email orchestration
- **SMTP Sender** (`email_sender_smtp.py`): Low-level email delivery
- **Template System**: Configurable email templates
- **Easy Integration**: Can be imported and used in any Python project

**Supported Operations**:
- Account verification emails
- Password reset emails
- Custom email sending

### 5. **Advanced Logging System**

Production-grade logging with multiple configuration options:

**Features** (`logging_config/log_manager.py`):
- **JSON Logging**: Structured logging for log analysis tools
- **File & Console Output**: Dual output capabilities
- **Application Filtering**: Separate logs for app and third-party packages
- **Log Rotation**: Prevents excessive disk usage (QueueLoggingManager)
- **Asynchronous Logging**: Queue-based logging for high performance
- **Customizable Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

**Classes**:
- `LoggingManager`: Basic logging configuration
- `QueueLoggingManager`: Asynchronous logging with queue

### 6. **JWT Token Management**

Secure token creation and verification:
- **Token Generation**: Automatic token creation for authenticated users
- **Token Verification**: Dependency-based verification on protected routes
- **Token Expiration**: Configurable token lifetime
- **Refresh Tokens**: Support for token renewal

**File**: `token_creater.py` - Token management utilities

### 7. **Database Abstraction (ORM)**

**SQLAlchemy Integration**:
- **Database Agnostic**: Switch between SQLite, PostgreSQL, MySQL, etc.
- **Zero Configuration**: Change only the connection string
- **No SQL Rewrites**: All database operations are automatically adapted
- **Migrations Support**: Schema changes without manual SQL
- **Relationship Management**: Automatic handling of foreign keys and relationships

**Supported Databases**:
- SQLite (default, included)
- PostgreSQL
- MySQL
- And many others...

**Usage**:
```python
# Change database by providing connection string in .env file
# From SQLite:
DB_CONNECTION_STRING = "sqlite+aiosqlite:///blog.db"

# To PostgreSQL:
DB_CONNECTION_STRING = "postgresql+asyncpg://user:password@localhost/blogblaze"

# All database queries remain unchanged!
```

**Files**:
- `models.py` - ORM models definition
- `database.py` - Session and connection management
- `config.py` - Configuration settings including database URL

### 8. **REST API Architecture**

Organized RESTful endpoints with clear separation:

- **Posts API** (`routers/api/posts.py`):
  - `GET /api/posts` - List all posts
  - `POST /api/posts` - Create new post
  - `GET /api/posts/{id}` - Get post details
  - `PUT /api/posts/{id}` - Update post
  - `DELETE /api/posts/{id}` - Delete post
  - `POST /api/posts/{id}/reviews` - Add review

- **Users API** (`routers/api/users.py`):
  - `POST /api/auth/register` - User registration
  - `POST /api/auth/login` - User login
  - `POST /api/auth/verify-email` - Email verification
  - `POST /api/auth/forgot-password` - Password reset request
  - `POST /api/auth/reset-password` - Password reset completion
  - `GET /api/users/{id}` - Get user profile

### 9. **Data Validation**

Using **Pydantic** for robust data validation:
- **Request Validation**: Automatic validation of incoming data
- **Response Serialization**: Consistent API responses
- **Type Safety**: Python type hints for better IDE support
- **Error Messages**: Clear validation error messages

**File**: `schemas.py` - All request/response schemas

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- pip (Python package manager)
- PostgreSQL (optional, for production use)

### Installation

1. **Clone and setup the project**:
```bash
cd BlogBlaze
pip install -r requirements.txt
```

2. **Configure the application**:
   - Edit `.env` to set your database URL and other settings
   - Configure email settings for SMTP
   - Set JWT secret key


3. **Run the application**:
```bash
python startserver.py
```

The application will be available at `http://localhost:8000`

## 🔒 Security Features

- **Password Hashing**: Bcrypt hashing for secure password storage
- **JWT Tokens**: Stateless authentication
- **Email Verification**: Prevents fake email registration
- **CSRF Protection**: Secure cookie handling
- **SQL Injection Prevention**: SQLAlchemy parameterized queries


## 📖 API Documentation

Comprehensive API documentation with:
- Request/response examples
- Authentication requirements
- Error codes and messages

Access at `/docs` (Swagger UI) or `/redoc` (ReDoc) when application is running.

## 🛠️ Configuration

Key configuration options in `config.py`:

```python
# Database
DATABASE_URL = "sqlite:///blog.db"

# JWT
JWT_SECRET_KEY = "your-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"

# Logging
LOG_LEVEL = "INFO"
LOG_IN_FILE = True
JSON_LOGS = False
```

## 🔄 Extending the Application

### Adding New Features

Thanks to the modular architecture, adding new features is simple:

1. **Create new service** in `data_services/`
2. **Create new API route** in `routers/api/`
3. **Add database model** in `models.py`
4. **Define schema** in `schemas.py`
5. **Update configuration** if needed

Existing code remains untouched!

### Customizing Modules

Modules are designed for easy customization:

- **Email Module**: Override email templates or SMTP settings
- **Logging Module**: Change log format or add custom filters
- **Auth Module**: Implement additional security layers
- **Database Layer**: Add custom queries or stored procedures

## 📊 Performance Considerations

- **Asynchronous Logging**: QueueLoggingManager for non-blocking logs
- **Database Connection Pooling**: Efficient database resource management
- **Caching Layer Ready**: Easy to add Redis or memcached
- **Pagination Support**: For large data sets
- **Query Optimization**: SQLAlchemy ORM best practices

## 🐛 Troubleshooting

### Database Connection Issues
- Verify DATABASE_URL 
- Check database server is running
- Ensure credentials are correct

### Email Not Sending
- Verify SMTP settings
- Check SMTP credentials
- Review logs in `logs/app.log`

### Authentication Failures
- Verify JWT_SECRET_KEY is set
- Check token expiration time
- Review auth logs

## 📝 Logging & Monitoring

All application activities are logged:

```
logs/
└── app.log          # Application and all logs
```

For production, configure:
- JSON logging for log aggregation tools
- Separate log files for different components
- Queue-based asynchronous logging

## 🤝 Contributing

This project demonstrates best practices for:
- Enterprise application structure
- Clean code principles
- Modular and scalable design
- Production-grade features

Feel free to use these patterns in your projects!

## 📄 License

This project is provided as-is for educational and reference purposes.

## 🙏 Acknowledgments

Built with:
- **FastAPI**: Modern web framework
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation
- **PyJWT**: JWT authentication
- **Jinja2**: Template engine

---

## Summary

BlogBlaze is not just a blogging platform—it's a **complete production-grade backend system** that can serve as:

- 🎓 A learning resource for enterprise architecture
- 🔧 A foundation for larger applications
- 📦 A modular toolkit for reusable components
- 📈 A scalable base for feature expansion

The clean architecture and modular design ensure that whether you're adding features, changing databases, or integrating with other systems, the codebase remains maintainable and extensible.

## 📸 Screenshots

User Registeration |  User Login
:-----------------:|:--------------:
![Register](screenshots/Register.png)   |  ![Login](screenshots/Login.png)


Forgot Password |  User Profile
:-----------------:|:--------------:
![Forgot Password](screenshots/Forgot%20Password.png) | ![User Profile](screenshots/userprofile.png) 


#### Home Page - Blog List
![Blog List](screenshots/bloglist.png)

