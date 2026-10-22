# Amazon Product Advertising API 5.0 (PA-API 5.0)

Foto **real** de cada producto, obtenida de la API oficial de Amazon: la unica via
permitida para mostrar la imagen concreta de un articulo en un sitio de afiliados.

## 1. Requisitos (en la cuenta de Amazon Afiliados)

1. Ser **afiliado aprobado** en el Programa de Afiliados de Amazon.es.
2. Solicitar acceso a la **Product Advertising API 5.0** en
   `afiliados.amazon.es -> Publicar -> API de publicidad de productos`.
   Si el menu no aparece, hay que pedirlo desde "Solicitar acceso a la API"
   (revision habitual de 48-72 h).
3. Crear **claves de AWS IAM** con permiso `AmazonProductAdvertisingAPI`
   (acciones `GetItems` y `SearchItems`).

## 2. Variables de entorno

| Variable | Valor | Obligatoria |
|---|---|---|
| `PAAPI_ACCESS_KEY` | clave publica de AWS IAM | si |
| `PAAPI_SECRET_KEY` | clave secreta de AWS IAM | si |
| `PAAPI_PARTNER_TAG` | `chollocesta-21` | no (por defecto) |
| `PAAPI_MARKETPLACE` | `www.amazon.es` | no |

En Zafiro las claves viven **fuera del repo**, en
`/data/user/0/com.niki914.zafiro/files/secrets/paapi_access_key` y
`.../paapi_secret_key` (permisos `600`). Ver `LEEME-paapi.txt` en esa carpeta.

## 3. Flujo

```bash
# 1) Validar la firma SigV4 contra los vectores oficiales de AWS
python scripts/paapi_client.py

# 2) Traer imagenes y metadatos de los ASIN del catalogo -> data/paapi_imagenes.json
python scripts/paapi_fetch_images.py

# 3) Sustituir los logotipos por la foto real en las paginas
python scripts/apply_paapi_images.py --dry-run   # simular
python scripts/apply_paapi_images.py
```

## 4. Automatizacion (GitHub Actions)

`.github/workflows/paapi-images.yml` ejecuta el flujo cada dia a las 07:17 y publica
los cambios. Necesita en `Settings -> Secrets and variables -> Actions`:
`PAAPI_ACCESS_KEY`, `PAAPI_SECRET_KEY`, `PAAPI_PARTNER_TAG`
(opcionalmente `PAAPI_MARKETPLACE` como variable).

## 5. Reglas de Amazon que respeta el script

- La imagen se muestra **enlazada al producto** (envoltorio `<a>` con el enlace de afiliado).
- La imagen **no se almacena ni se copia**: se sirve desde la URL que devuelve la API.
- **No se recorta ni se distorsiona**: `object-fit: contain`.
- El pie indica "Imagen del producto - Amazon" con enlace al articulo.
- La foto real sustituye al logotipo solo cuando la API devuelve el articulo exacto.

## 6. Ficheros

| Fichero | Contenido |
|---|---|
| `scripts/paapi_client.py` | cliente PA-API 5.0 con firma AWS SigV4 (solo stdlib) |
| `scripts/paapi_fetch_images.py` | GetItems/SearchItems -> `data/paapi_imagenes.json` |
| `scripts/apply_paapi_images.py` | aplica las fotos reales a las paginas |
| `data/productos_paapi.json` | catalogo: pagina -> {figura, nombre, asin} |
| `data/paapi_imagenes.json` | resultado de la consulta (generado, no versionado) |

### Formato del catalogo

`data/productos_paapi.json` empareja cada figura con su ASIN mediante el **indice de
la figura** (`figura`), no por busqueda de texto: los enlaces de Amazon pueden ser
cortos (`amzn.to`) y no aparecen como ASIN en el HTML.

```json
"ambientador.html": [
  { "figura": 1, "nombre": "Air Wick Essential Mist Difusor...", "asin": "B0F9LD6GVB" }
]
```

Si anades productos, regenera el catalogo con el extractor de ASIN (mismo criterio
que `scripts/fetch_logos.py` pero sobre los enlaces de Amazon) y mantén el indice
coherente con el orden de las figuras de la pagina.

## 7. Nota sobre `m.media-amazon.com`

Con la PA-API activada, el sitio si enlaza imagenes servidas por Amazon
(`m.media-amazon.com`), pero **solo** las que devuelve la propia API, enlazadas al
producto y sin almacenarlas. Es la excepcion prevista por el Programa de Afiliados;
el resto de imagenes del sitio siguen viniendo de Wikimedia Commons.
