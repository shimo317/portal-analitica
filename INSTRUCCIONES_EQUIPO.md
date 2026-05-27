# 🚀 Instrucciones para ejecutar el Portal de Analítica (Equipo)

¡Hola equipo! Sigan estos 4 pasos para tener una copia exacta del sistema corriendo localmente en sus computadoras, incluyendo la base de datos y todos los requerimientos de Python.

---

## Paso 1: Instalar y configurar PostgreSQL
El portal necesita una base de datos PostgreSQL local para guardar usuarios y logs de manera segura. Afortunadamente, ¡el código ya crea las tablas automáticamente! Sólo necesitas crear la estructura en blanco.

1. Descarga e instala **PostgreSQL** desde su página oficial (https://www.postgresql.org/download/).
2. **⚠️ MUY IMPORTANTE:** Durante la instalación, te pedirá que asignes una contraseña para el superusuario (`postgres`). Asegúrate de escribir exactamente: `Admin123#` (ya que es la contraseña que configuramos internamente).
3. Abre **pgAdmin 4** (se instala con PostgreSQL).
4. Crea una base de datos vacía que se llame exactamente: `portal_analitica`.

---

## Paso 2: Preparar el entorno de Python
Debes tener Python (versión 3.9 o superior) instalado en tu computadora.

1. Abre tu terminal (Símbolo del sistema o PowerShell) y navega a la carpeta principal donde está este proyecto (donde se encuentra `Home.py`).
2. (Opcional pero recomendado) Crea un entorno virtual para no ensuciar tu computadora:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Instala todas las dependencias y librerías que utiliza nuestro portal ejecutando:
   ```bash
   pip install -r requirements.txt
   ```

---

## Paso 3: Arrancar el portal
1. En tu misma terminal (asegurándote de estar en la carpeta donde está `Home.py`), ejecuta el siguiente comando:
   ```bash
   streamlit run Home.py
   ```
2. ¡Listo! Se abrirá automáticamente una pestaña nueva en tu navegador.

---

## Paso 4: Iniciar sesión por primera vez
Dado que la base de datos estaba vacía, el sistema ha creado automáticamente la cuenta administradora maestra para que no te quedes fuera. 

Puedes ingresar con:
- **Usuario:** `admin` (o `admin@portal.local`)
- **Contraseña:** `Admin123#`

Desde ahí, puedes ir al *Panel de Administración* y experimentar agregando nuevos usuarios de prueba (Ventas, Operación, etc).

¡Éxito con sus pruebas! Cualquier duda sobre la arquitectura, revisen la lógica de inicialización que tenemos en `auth.py`.
