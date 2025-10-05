# Usa una imagen base de Python ligera
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requisitos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación
COPY . .

# Expone el puerto por defecto de Flask
EXPOSE 5000

# Comando para iniciar la aplicación
# Usa el host 0.0.0.0 para que sea accesible dentro de Docker
CMD ["flask", "run", "--host=0.0.0.0"]