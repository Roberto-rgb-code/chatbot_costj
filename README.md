Pasos para configurar el entorno
Clonar o descargar el proyecto Si estás trabajando con un repositorio, clónalo o descárgalo a tu máquina:
text

Contraer

Ajuste

Copiar
git clone (https://github.com/Roberto-rgb-code/chatbot_costj.git)
cd (https://github.com/Roberto-rgb-code/chatbot_costj.git)
Crear un entorno virtual En la carpeta del proyecto, ejecuta el siguiente comando para crear un entorno virtual llamado venv:
text

Contraer

Ajuste

Copiar
python -m venv venv
Activar el entorno virtual Dependiendo de tu sistema operativo, usa uno de estos comandos:
Windows:
text

Contraer

Ajuste

Copiar
venv\Scripts\activate
Linux/MacOS:
text

Contraer

Ajuste

Copiar
source venv/bin/activate
Una vez activado, deberías ver (venv) al inicio de la línea en tu terminal.
Instalar las dependencias Con el entorno activado, instala los paquetes listados en el archivo requirements.txt:
text

Contraer

Ajuste

Copiar
pip install -r requirements.txt
Verificar la instalación Asegúrate de que todo funcione ejecutando el script principal o un comando de prueba (si aplica), por ejemplo:
text

Contraer

Ajuste

Copiar
python app.py
Desactivar el entorno (opcional) Cuando termines, puedes salir del entorno virtual con:
text

Contraer

Ajuste

Copiar
deactivate
Notas adicionales
Si necesitas agregar nuevas dependencias, instálalas con pip install <nombre_del_paquete> y actualiza el archivo requirements.txt con:
text

Contraer

Ajuste

Copiar
pip freeze > requirements.txt
Para problemas comunes, revisa la documentación de las librerías o el archivo de ayuda del proyecto.
¡Listo! Ahora deberías tener el entorno configurado y las dependencias instaladas.