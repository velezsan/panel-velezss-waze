# Cómo se actualizan los URs del panel

La página de URs es `docs/urs.html` y sus datos `docs/urs-datos.json`. Los datos no los
produce el escáner: se leen del editor de Waze con el navegador y se suben a mano por la
ruta de subida de GitHub. Toda la corrida toma unos cuatro minutos.

Para pedirlo basta con decir «actualiza los URs». Lo único que hace falta del lado tuyo es
que en el Chrome donde vive la extensión estén vivas dos sesiones: la del WME y la de
GitHub (la cuenta `velezsan`). Si la de GitHub se cae, la página de subida dice «Uploads
are disabled» y hay que volver a firmar; es lo único que no se puede hacer por ti.

Este archivo existe para que cualquier sesión nueva pueda repetir el proceso sin volver a
investigarlo, porque la mitad del trabajo fue entender la API del editor.

## Reglas que no se rompen

Del editor **solo se lee**. Nunca se llama `setReadMapUpdateRequest`, ni se responde ni se
cierra un UR: eso lo sigues haciendo tú. Tampoco se le da clic a un renglón de la lista del
editor, porque con eso el WME marca el UR como leído.

El `git push` a `velezsan/panel-velezss-waze` está bloqueado (el proxy responde 403), así
que todo se publica por el navegador. Los commits locales son nada más una copia de
trabajo.

**Nada de archivos nuestros dentro de `docs/data/`.** El escáner publica con
`git add -A docs/data`, y como el runner no tiene esos archivos en su copia, los ve como
borrados y los quita en su siguiente publicación. Así desapareció `docs/data/urs.json` el 12
de octubre. Por eso los datos viven en `docs/urs-datos.json`, fuera de esa carpeta.

## 1. Capturar el filtro

Se abre el editor en `https://www.waze.com/es-419/editor?env=row&lat=19.4326&lon=-99.1332&zoomLevel=16&tab=issue_tracker`,
se instala un hook de `fetch` que guarde el cuerpo de las llamadas a
`/row-Descartes/grpc/com.waze.mapeditor.web.api.MapEditorWebServer/searchMapUpdateRequests`,
se elige el filtro guardado en el desplegable y se pica refrescar. El cuerpo que no trae
bbox (unos 80 a 90 caracteres en base64) es la base de todas las peticiones.

Los filtros guardados que se usan son **TodoMX** para los abiertos y **TodoMX (Con
Cerrados)** cuando además se quieren los reportes de los champs.

## 2. Barrer el país

Las incidencias ya no viven en el JSON viejo: los URs, los MP y los MS se movieron a gRPC y
solo los PUR siguen en `Issues/Search/List`. El transporte es gRPC-web-text: el cuerpo va en
base64 y la respuesta vuelve en binario, así que se lee con `arrayBuffer`, no con `text`.
Las cabeceras son `content-type: application/grpc-web-text`, `x-grpc-web: 1` y
`x-user-agent: grpc-web-javascript/0.1`, y cada trama lleva un byte de bandera y cuatro de
largo.

En la petición, el campo 1 es el filtro, el 2 el límite (el servidor topa en **500** aunque
se le pida más), el 3 el offset (**lo ignora**, por eso no sirve paginar) y el 5 el orden.
Dentro del filtro, `1.1.1` y `1.1.2` son las esquinas del bbox como `{101: lon×1e6,
102: lat×1e6}` —varint con signo, los negativos en complemento a dos—, `1.1.5` es el país
(México es **145**) y `1.2` el filtro de URs: si trae `1.2.5` con valor 1 son solo abiertos,
y si no viene trae abiertos y cerrados.

Como el offset no sirve, la cobertura se hace por mosaico: celdas de 2° sobre longitud −118
a −86 y latitud 14 a 33, y la celda que devuelva 500 se parte en cuatro y se vuelve a pedir.
Con cuatro peticiones en paralelo son unos 15 segundos y 160 peticiones para los abiertos
(cerca de mil URs), y unos 50 segundos y 280 peticiones para abiertos más cerrados (cerca de
veinte mil, que es el histórico de unos ocho meses).

De cada registro se usan: el campo 1 (id), el 2.2 (el punto, dos dobles con longitud y
latitud), el 4 (tipo), el **6 (1 si está abierto, 2 si está cerrado)**, el 8 (quien reportó,
con id y usuario), el 9 (último editor), el 10 y el 11 (creado y actualizado, en segundos) y
el 20, que trae país, estado y ciudad ya resueltos por Waze.

Los tipos van corridos cinco lugares contra la numeración de i18n: 1 giro incorrecto,
2 dirección incorrecta, 3 ruta incorrecta, 4 falta rotonda, 5 error general, 6 giro no
permitido, 7 cruce incorrecto, 8 puente faltante, 9 sentido de conducción incorrecto,
10 falta salida y 11 falta calle.

## 3. Las descripciones

La lista no trae la descripción: hay que pedir cada UR aparte con `getMapUpdateRequest`,
mandando `{1: id, 2: máscara}` donde la máscara es un repetido de cadenas con `id` y
`comments`. En la respuesta cada campo 17 es un comentario con usuario, fecha y texto, y la
descripción es el del `Reporter`. Con seis en paralelo, mil cien URs salen en un minuto.
Conviene pedirla solo para lo que se va a publicar, y vale saber que apenas una quinta parte
trae texto: el resto nunca contestó la pregunta del Map_Team.

## 4. Los reportes de los champs

La lista de local champs sale de `docs/data/champs.json`, de la llave `totales`, y se cruza
contra el usuario de quien reportó sin distinguir mayúsculas. Esa vista va con los cerrados
incluidos y lleva una columna extra que vale 1 si el UR sigue abierto.

## 5. Publicar

El JSON lo arma la página de Waze, así que hay que cruzarlo a GitHub. Lo único que cruza
orígenes sin pedirte nada es **`postMessage`**: el portapapeles y Ctrl+V no sirven porque
las pestañas de la sesión están en segundo plano. Desde la pestaña del WME, un botón
inyectado abre `window.open('https://github.com/velezsan/panel-velezss-waze/upload/main/docs','svsgh')`
—el clic sintético cuenta como activación de usuario—, se inyecta un
`addEventListener('message', …)` en esa pestaña y se manda el texto con
`postMessage({svs:1, txt:JSON}, 'https://github.com')`.

La página HTML va al revés, de la máquina al navegador, y ahí sale mucho más barato mandar
un parche que el archivo entero: se calculan operaciones de líneas con
`difflib.SequenceMatcher` contra `git show HEAD:docs/urs.html`, se pasan como JSON en dos
trozos de unos 2,500 caracteres, se baja el archivo publicado desde
`raw.githubusercontent.com` (ese sí manda CORS) y se aplican. **Siempre se verifica con
SHA-256** que el viejo era el esperado y que el nuevo coincide con la copia local antes de
subir nada.

La subida es en `/upload/main/<carpeta>`: se arma un `File`, se suelta sobre el elemento
`file-attachment` con `DataTransfer` y los eventos `dragenter`, `dragover` y `drop`, se
escribe el mensaje en `#commit-summary-input` usando el setter nativo de `value` más un
evento `input`, y se pica el último botón «Commit changes» que esté habilitado. Se pueden
soltar varios archivos para que vayan en un mismo commit.

## 6. Comprobar

GitHub Pages tarda cerca de un minuto en reconstruir. Después se abre la página publicada y
se leen las tarjetas y la tabla con JavaScript, porque una captura no alcanza para
verificar. El commit se confirma en
`https://api.github.com/repos/velezsan/panel-velezss-waze/commits`. Al final se deja el
commit local, sin push, y un resumen con los números del día: abiertos, cuántos no ha
contestado nadie, cuántos están por cerrarse solos a los 30 días, cuántos traen descripción
y cuántos reportaron los champs.
