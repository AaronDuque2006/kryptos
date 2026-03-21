# Password Manager TUI

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

Para poder instalar y ejecutar este proyecto correctamente debes tener instalados en tu sistema local:
1. Python 3.12 o superior.
2. El gestor de paquetes y entornos virtuales `uv` (recomendado) o `pip`.
3. Git (para clonar el repositorio).

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
4. Para ejecutar la suite de pruebas enfocada en temas de seguridad y arquitectura: `uv run python -m unittest discover -s tests`
