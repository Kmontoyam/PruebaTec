# API Postcodes Integration

## Arquitectura
La solución consta de dos microservicios:
1. Microservicio 1: Recibe el archivo CSV, extrae las coordenadas y las almacena en la base de datos. También se comunica con el Microservicio 2 para obtener los códigos postales.
2. Microservicio 2: Consume la API de Postcodes.io para obtener el código postal más cercano a las coordenadas recibidas.

## Ejecución
1. Clonar este repositorio.
2. Ejecutar `docker-compose up --build` para levantar los servicios.
3. Utilizar el endpoint `/upload` del Microservicio 1 para enviar el archivo CSV.
