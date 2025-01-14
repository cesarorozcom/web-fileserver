#!/bin/bash
# Actualiza los paquetes e instala git y pip
sudo yum update -y
sudo yum install -y git python3-pip

# Clona el repositorio desde GitHub
git clone https://github.com/cesarorozcom/web-fileserver.git /home/ec2-user/web-fileserver

# Navega al directorio del proyecto
cd /home/ec2-user/web-fileserver

# Instala las dependencias del proyecto
pip3 install -r requirements.txt

# Crea el archivo de configuración de la aplicación
cat <<EOF > app.ini
[aws_prd]
role_arn=
bucket_name=
region=

[webapp]
secret_key=
EOF

# Instala Gunicorn y ejecuta la aplicación
pip3 install gunicorn
nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app &