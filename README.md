# Generador de acreditaciones con códigos QR únicos

Este repositorio contiene scripts utilizados para generar acreditaciones con códigos QR únicos como las que utilizamos en el [HackUDC](https://hackudc.gpul.org), organizado por [GPUL](https://gpul.org).

Este script generará acreditaciones de varios tipos con QRs únicos. La salida acabará en el directorio `out/`, donde habrá un pdf para cada tipo de acreditaciones. El pdf tendrá una página por acreditación y el reverso en la última página.

## Requisitos

Este script espera producir cuatro tipos de acreditaciones `hacker`, `mentor`, `organizacion` y `patrocinador`. Debes incluír en directorio `in/` un svg para cada tipo de acreditación, que será el anverso.

*Recuerda dibujar un recuadro blanco para el fondo del QR, ya que si no no será legible si el fondo de tu diseño es oscuro. También es recomendable que dejes un pequeño margen conocido como "quiet zone" para facilitar la lectura del código*

En `in/reversos/` debes incluír los reversos de la acreditaciones en pdf.

*Este repositorio incluye archivos de ejemplo en el direcotorio `in/`. Se trata de las acreditaciones de [HackUDC 2025](https://hackudc2025.gpul.org). Gracias a [@migueldeoleiros](https://github.com/migueldeoleiros) por permitirme publicar aquí las acreditaciones que utilizan de fondo la tesela que diseñó*

## Uso

Para generar las acreditaciones debes ejecutar los scripts en el siguiente orden:

### 1. Generar los tokens para los códigos QR

Con el script `generar_csv.py` puedes generar un csv con los códigos aleatorios para las acreditaciones. Puedes cambiar el número de acreditaciones de cada tipo cambiando la variable `CANTIDADES`. Ejecuta el script.

### 2. Generar los códigos QR

A continuación, generaremos los códigos QR que superpondremos en las acreditaciones. Ejecuta el script `generar_qr.py`

#### 2.1. Colorear los códigos QR

El script `cambiar_color.sh` colorea los códigos QR según su tipo, para que coincidan mejor con el diseño de las acreditaciones. Para cambiar el color edita el valor en hexadecimal de las cuatro últimas líneas del código.

### 3. Generar las acreditaciones

El siguiente paso es generar las acreditaciones con los códigos QR que generamos antes. El script `overlay.sh` generará todas las acreditaciones con sus códigos QR en svg.

Para modificar la posición del código QR puedes modificar la variable `pos` en el script `overlay.py`. La variable es una tupla de 3 valores: `x`, `y` y `escala`. Siendo los dos primeros valores la posición del QR en el anverso y el último la escala sobre 1 para el código QR.

En el ejemplo puedes ver que la posición es una resta. Esto se debe a que el QR generado contiene un espacio para la quiet zone, que hay que restar para que la esquina del código QR esté en el lugar deseado. En el ejemplo el valor es de 2.759 ya que la quiet zone es de 4mm, y esto varía al escalar todo el QR.

#### 3.1. Convertir a pdf

El script `pdf.sh` renderizará las acreditaciones a archivos pdf individuales. Puedes unir todas las acreditaciones de un mismo tipo en un único archivo pdf ejecutando `mix.sh`

### 4. Añadir los reversos

Por último, añade los reversos para las acreditaciones con el script `final.sh`. El resultado serán cuatro PDFs, uno por tipo de acreditación, que contendrán una página para cada acreditación y el reverso en la última página.
