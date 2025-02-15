# Documentación de la Base de Datos

## Descripción General

La base de datos está diseñada para gestionar usuarios, lugares, procesamiento de imágenes satelitales y detección de deforestación. Utiliza PostgreSQL con la extensión PostGIS para el manejo de datos geoespaciales.

## Tablas

### 1. users
Almacena la información de los usuarios del sistema.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer (PK) | Identificador único del usuario |
| email | String (unique) | Correo electrónico del usuario (único) |
| hashed_password | String | Contraseña encriptada |
| full_name | String | Nombre completo del usuario |
| is_active | Boolean | Estado de activación de la cuenta |
| created_at | DateTime | Fecha de creación del usuario |
| updated_at | DateTime | Fecha de última actualización |

### 2. places
Almacena los lugares o áreas de interés definidos por los usuarios.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer (PK) | Identificador único del lugar |
| name | String | Nombre del lugar |
| description | String | Descripción del lugar |
| geometry | Geometry(POLYGON) | Geometría del polígono (PostGIS) |
| user_id | Integer (FK) | ID del usuario propietario |
| created_at | DateTime | Fecha de creación |
| updated_at | DateTime | Fecha de última actualización |

Índices:
- `idx_places_geometry`: Índice espacial GiST para búsquedas geográficas eficientes

### 3. processing_batches
Registra los lotes de procesamiento para detección de cambios.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer (PK) | Identificador único del lote |
| area_of_interest | Geometry(POLYGON) | Área a procesar |
| start_date | DateTime | Fecha inicial del período |
| end_date | DateTime | Fecha final del período |
| status | String | Estado del procesamiento (pending, processing, completed, failed) |
| processed_at | DateTime | Fecha de inicio del procesamiento |
| completed_at | DateTime | Fecha de finalización |
| error_message | String | Mensaje de error (si existe) |
| user_id | Integer (FK) | ID del usuario que inició el proceso |
| place_id | Integer (FK) | ID del lugar asociado (opcional) |

Índices:
- `idx_processing_batches_area`: Índice espacial GiST para el área de interés

### 4. deforestation_events
Almacena los eventos de deforestación detectados.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer (PK) | Identificador único del evento |
| affected_area | Geometry(POLYGON) | Área afectada por deforestación |
| detected_at | DateTime | Fecha de detección |
| confidence_score | Float | Puntuación de confianza (0-1) |
| area_hectares | Float | Área afectada en hectáreas |
| batch_id | Integer (FK) | ID del lote de procesamiento |

Índices:
- `idx_deforestation_events_area`: Índice espacial GiST para el área afectada

## Relaciones

1. `users` ← `places`:
   - Un usuario puede tener múltiples lugares
   - Cada lugar pertenece a un usuario

2. `users` ← `processing_batches`:
   - Un usuario puede tener múltiples lotes de procesamiento
   - Cada lote pertenece a un usuario

3. `places` ← `processing_batches`:
   - Un lugar puede tener múltiples lotes de procesamiento
   - Cada lote puede estar asociado a un lugar (opcional)

4. `processing_batches` ← `deforestation_events`:
   - Un lote puede tener múltiples eventos de deforestación
   - Cada evento pertenece a un lote

## Consideraciones Espaciales

- Todas las geometrías utilizan SRID 4326 (WGS 84)
- Se utilizan índices espaciales GiST para optimizar consultas geográficas
- La extensión PostGIS permite operaciones espaciales como:
  - Intersección de áreas
  - Cálculo de áreas
  - Búsqueda por proximidad
  - Validación de geometrías

## Mantenimiento

- Las migraciones se gestionan con Alembic
- Los índices espaciales se crean automáticamente en las migraciones
- La tabla `spatial_ref_sys` es gestionada por PostGIS y no debe modificarse 