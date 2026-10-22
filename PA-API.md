# Amazon Product Advertising API 5.0 (PA-API 5.0)

Foto **real** de cada producto, obtenida de la API oficial de Amazon. Es la unica via
permitida para mostrar la imagen concreta de un articulo dentro de un sitio de afiliados.

## 1. Requisitos (en la cuenta de Amazon Afiliados)

1. Ser **afiliado aprobado** en el Programa de Afiliados de Amazon.es.
2. Solicitar acceso a la **Product Advertising API 5.0** en
   `afiliados.amazon.es -> Publicar -> API de publicidad de productos`.
   Amazon concede el acceso segun el nivel de ventas; si no aparece el menu, hay que
   pedirlo desde el enlace de "Solicitar acceso a la API" (suele revisarse en 48-72 h).
3. Crear unas **claves de AWS IAM** con permiso para la API:
   - Usuario -> Seguridad -> Crear clave de acceso.
   - Permiso: `AmazonProductAdvertisingAPI` (acciones `GetItems` y `SearchItems`).

## 2. Variables de entorno

| Variable | Valor | Obligatoria |
|---|---|---|
| `PAAPI_ACCESS_KEY` | clave publica de AWS IAM | si |
| `PAAPI_SECRET_KEY` | clave secreta de AWS IAM | si |
| `PAAPI_PARTNER_TAG` | `chollocesta-21` | no (por defecto) |
| `PAAPI_MARKETPLACE` | `www.amazon.es` | no |
| `PAAPI_REGION` | `eu-west-1` (se deriva del marketplace) | no |

En Zafiro las claves se guardan **fuera del repo**, en `/data/user/0/com.niki914.zafiro/files/secrets/`,
con permisos `600`. Nunca se escriben en el codigo, en la memoria ni en este repositorio.

## 3. Uso

```bash
# 1) Validar la firma SigV4 contra los vectores oficiales de AWS
python scripts/paapi_client.py

# 2) Traer imagenes y metadatos de los ASIN del catalogo
python scripts/paapi_fetch_images.py

# 3) Sustituir los logotipos por la foto real del producto
python scripts/apply_paapi_images.py --dry-run   # simular
python scripts/paapi_fetch_images.py && python scripts/apply_paapi_images.py
```

El resultado se guarda en `data/paapi_imagenes.json` (ASIN -> imagen, titulo, precio, URL).

## 4. Reglas de Amazon que respeta el script

- La imagen se muestra **enlazada al producto** (envoltorio `<a>` con el enlace de afiliado).
- La imagen **no se almacena ni se copia**: se sirve desde la URL que devuelve la API.
- **No se recorta ni se distorsiona**: se usa `object-fit: contain`.
- El pie indica "Imagen del producto - Amazon" con enlace al articulo.
- La imagen real sustituye al logotipo solo cuando la API devuelve el articulo exacto.

## 5. Automatizacion con GitHub Actions

Anadir en `Settings -> Secrets and variables -> Actions`:
`PAAPI_ACCESS_KEY`, `PAAPI_SECRET_KEY` y `PAAPI_PARTNER_TAG`.
El flujo de trabajo puede ejecutar `paapi_fetch_images.py` y `apply_paapi_images.py`
y publicar el resultado en `data/paapi_imagenes.json`.

## 6. Ficheros

| Fichero | Contenido |
|---|---|
| `scripts/paapi_client.py` | cliente PA-API 5.0 con firma AWS SigV4 (solo biblioteca estandar) |
| `scripts/paapi_fetch_images.py` | consulta GetItems/SearchItems y guarda `data/paapi_imagenes.json` |
| `scripts/apply_paapi_images.py` | sustituye los logotipos por la foto real en las paginas |
| `data/productos_paapi.json` | catalogo pagina -> producto -> ASIN |
| `data/paapi_imagenes.json` | resultado de la consulta (se genera, no se versiona) |
