tui_password_manager/
│
├── core/                       # Lógica central y seguridad
│   ├── __init__.py
│   ├── crypto.py               # Encriptación, KDF (Argon2/PBKDF2)
│   ├── generator.py            # Generación segura de contraseñas (secrets)
│   └── security_utils.py       # Limpieza de memoria, borrado de portapapeles
│
├── db/                         # Persistencia de datos
│   ├── __init__.py
│   ├── database.py             # Conexión a SQLite y setup de tablas
│   └── repositories.py         # Clases para manejar CRUD de Usuarios y Bóveda
│
├── models/                     # Estructuras de datos (Data Classes o Pydantic)
│   ├── __init__.py
│   ├── user.py                 # Modelo de Usuario
│   └── credential.py           # Modelo de Credencial/Entrada de la bóveda
│
├── services/                   # Casos de uso / Lógica de negocio
│   ├── __init__.py
│   ├── auth_service.py         # Manejo de login y registro
│   └── vault_service.py        # Intermediario entre UI, Crypto y DB
│
├── ui/                         # Componentes de la interfaz de texto (Textual)
│   ├── __init__.py
│   ├── app.py                  # Aplicación principal de Textual
│   ├── screens/                # Pantallas individuales
│   │   ├── login_screen.py
│   │   ├── register_screen.py
│   │   └── dashboard_screen.py
│   └── widgets/                # Componentes reutilizables (botones, tablas)
│
├── tests/                      # Pruebas unitarias
│   ├── test_crypto.py
│   ├── test_generator.py
│   └── test_db.py
│
├── main.py                     # Punto de entrada de la aplicación
├── requirements.txt            # Dependencias (textual, cryptography, pyperclip...)
└── .gitignore