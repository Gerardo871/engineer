--instalar dependecias
sudo dnf groupinstall "Development Tools"
sudo dnf install python3.11-devel
 
---crear carpeta para superset
mkdir /superset
 
---crear entorno virtual
python3 -m venv venv
 
--activar entorno virtual
source /superset/venv/bin/activate
 
---actualizar pip
pip install --upgrade pip
 
--instalar superset
pip install apache-superset
pip install gevent
 
--instalacion de postgres
sudo dnf install postgresql-server postgresql-contrib
sudo dnf install postgresql-devel
 
--instalacion de redis
sudo dnf install redis
 
-----configurar redis
sudo systemctl start redis
sudo systemctl enable redis
sudo vim /etc/redis.conf
##cambiar en daemonize no ---> daemonize yes
##cambiar en protected-mode yes --> protected-mode no
### comentar bind 127.0.0.1 --> #bind 127.0.0.1
 
-----crear base de datos
sudo postgresql-setup initdb
vim /etc/postgresql-setup/upgrade/postgresql.conf
agregar --> listen_addresses = '*'
debajo de --> # - Security and Authentication -
sudo vim /var/lib/pgsql/data/pg_hba.conf
agregar la sigueinte linea en el final del archivo ---> host all all 0.0.0.0/0  md5
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -u postgres psql
CREATE DATABASE superset_db;
CREATE ROLE superset_role WITH LOGIN PASSWORD 'superset';
GRANT ALL PRIVILEGES ON DATABASE superset_db TO superset_role;
CREATE USER superset_user WITH PASSWORD 'superset';
GRANT superset_role TO superset_user;
 
---abrir puertos 
sudo firewall-cmd --permanent --zone=public --add-port=6378/tcp
sudo firewall-cmd --permanent --zone=public --add-port=5432/tcp
sudo firewall-cmd --permanent --zone=public --add-port=8088/tcp
 
 
sudo systemctl restart firewalld

---exportamos variable de entorno
export SUPERSET_CONFIG_PATH=/superset/superset_config.py
 
--iniciar db superset
superset db upgrade
superset init
 
-----crear usuario admin
superset fab create-admin
 
 
---levantar proyecto
gunicorn -w 8 -k gevent --worker-connections 500 --timeout 900 -b  0.0.0.0:8088  "superset.app:create_app()" --daemon
celery --app=superset.tasks.celery_app:app worker --pool=prefork -O fair -c 1 --detach
celery --app=superset.tasks.celery_app:app beat --detach