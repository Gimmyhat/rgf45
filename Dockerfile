FROM continuumio/miniconda3


RUN conda install -y python=3.9
RUN conda install -y jinja2 pyproj pyyaml psutil pydantic=1.9.0
RUN conda install -y -c conda-forge untangle
RUN conda install -y psycopg2
RUN conda install -y gdal=3.0.2
RUN conda install -y libgdal=3.0.2
RUN pip install flask waitress patool flask-httpauth python-dotenv

# Установка 7-Zip
# Добавляем non-free репозитории для Debian Bullseye
RUN echo "deb http://deb.debian.org/debian bullseye main contrib non-free" > /etc/apt/sources.list && \
    echo "deb-src http://deb.debian.org/debian bullseye main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bullseye-security main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bullseye-updates main contrib non-free" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y p7zip-full p7zip-rar && \
    rm -rf /var/lib/apt/lists/*

COPY . /main
WORKDIR /main

ENV PYTHONPATH "${PYTHONPATH}:/main"