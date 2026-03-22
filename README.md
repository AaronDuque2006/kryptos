# Kryptos Password Manager TUI

## Descripcion del Proyecto
Esta aplicacion es un gestor de contraseñas altamente seguro ejecutado enteramente desde la terminal mediante una interfaz de usuario en modo texto (TUI) construida con la libreria Textual.

El objetivo de este proyecto es proveer un entorno seguro, rapido y local donde los usuarios puedan almacenar, organizar y consultar sus credenciales (nombres de usuario, contraseñas, URLs y notas) sin depender de servicios en la nube de terceros. 

Las caracteristicas de seguridad incluyen:
- Autenticacion robusta utilizando el algoritmo Argon2 (ganador del Password Hashing Competition) para verificar la contraseña maestra.
- Encriptacion de grado militar utilizando AES-GCM (256-bit) para todo el contenido de la boveda.
- Derivacion de claves utilizando el estandar aprobado por NIST, PBKDF2HMAC con millones de iteraciones y sales exclusivas por usuario.
- "Zero-Knowledge" local: La informacion matematica utilizada para el inicio de sesion es completamente diferente a la utilizada para desencriptar tu informacion, garantizando que tu llave nunca se guarde.
- Base de datos relacional local basada en SQLite gestionada mediante SQLModel.

---

## Requisitos Previos

Para poder instalar y ejecutar este proyecto correctamente en tu sistema operativo, es necesario contar con `uv`. Se trata de un gestor de paquetes y proyectos hiper-rapido para Python que automatiza la creacion de comandos terminales.

### Como verificar si ya tienes `uv` instalado

Abre tu terminal y ejecuta el siguiente comando:
```bash
uv --version
```
Si la terminal te responde con un numero de version (por ejemplo, `uv 0.1.x`), estas listo para proceder a la Instalacion Global.

### Como instalar `uv` si no lo tienes

Si el comando anterior arrojo un error, elige el metodo correspondiente a tu sistema operativo para instalar `uv` de manera oficial:

- **Windows (En PowerShell):**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

- **macOS y Linux:**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

*(Alternativa: Si ya cuentas con un entorno de Python antiguo configurado, tambien es posible instalar uv ejecutando simplemente `pip install uv`).*

---

## Proceso de Instalacion Global

Para utilizar la aplicacion de manera nativa en tu sistema operativo, no necesitas clonar tu mismo el codigo. El gestor descargara y compilara todo por ti en un solo paso.

Ejecuta el siguiente comando en tu terminal:

```bash
uv tool install git+https://github.com/AaronDuque2006/kryptos.git
```

Una vez finalizado el proceso, el sistema habra creado un comando global para todo el SO conectado al nucleo de la aplicacion.

---

## Actualizaciones

Cuando exista una nueva version del software o un parche de seguridad, puedes actualizar toda la herramienta escribiendo un solo comando en la terminal:

```bash
uv tool upgrade kryptos-password-manager
```

---

## Como Ejecutar y Utilizar la Aplicacion

Tras haber seguido el proceso de instalacion global, ya puedes correr la aplicacion desde cualquier ubicacion y ruta dentro tu terminal. 

Simplemente ejecuta el siguiente comando:
```bash
kryptos
```

### Primeros pasos dentro de la TUI:
1. Si es tu primera vez ejecutando la aplicacion, selecciona la opcion de registrar a un usuario e ingresa una contraseña maestra fuerte.
   (Es vital que recuerdes esta contraseña, ya que es la llave criptografica unica que encripta toda tu base de datos local; no puede recuperarse si la pierdes).
2. Tras registrarte (o tras iniciar sesion si ya posees una cuenta), accederas a la boveda principal.
3. Utiliza la interfaz visual intuitiva de la terminal para agregar nuevas credenciales (Title, User, Password, URL, Notes)
4. Puedes copiar de inmediato todas tus credenciales desencriptadas y gestionarlas desde el panel de busqueda.

---

## Entorno de Desarrollo y Tests

Si deseas modificar el codigo fuente de la aplicacion localmente, la manera sugerida de ejecutarla es:

1. Clonar el repositorio: `git clone https://github.com/AaronDuque2006/kryptos.git`
2. Para sincronizar las dependencias e instalar el entorno virtal: `uv sync`
3. Para correr la aplicacion sin instalar globalmente: `uv run kryptos` o `uv run main.py`
4. Para instalar dependencias de testing (pytest y cobertura): `uv sync --extra test`
5. Para ejecutar toda la suite de pruebas: `uv run pytest`

### Cobertura de la suite de pruebas

La suite automatizada actual valida flujos criticos de seguridad y estabilidad:

- Seguridad de la boveda y manejo de cifrado/descifrado ante datos alterados.
- Validaciones de autenticacion (username/password) en registro y login.
- Rate limiting en autenticacion para bloquear intentos repetidos fallidos.
- Timeout de sesion por inactividad para cierre automatico seguro.

Estas pruebas son rapidas y deterministas para facilitar su ejecucion local y en CI en cada push/PR.

## Calidad de código

Para validar calidad de forma consistente en local:

1. Instalar dependencias de calidad y testing:
   ```bash
   uv sync --extra test --extra quality
   ```
2. Ejecutar lint con Ruff:
   ```bash
   uv run ruff check .
   ```
3. Ejecutar type checking con Mypy:
   ```bash
   uv run mypy
   ```
4. Ejecutar tests con cobertura mínima (75% sobre `core`, `models` y `services`):
   ```bash
   uv run pytest --cov=core --cov=models --cov=services --cov-report=term-missing --cov-fail-under=75
   ```

Comando combinado recomendado:

```bash
uv run ruff check . && uv run mypy && uv run pytest --cov=core --cov=models --cov=services --cov-report=term-missing --cov-fail-under=75
```
