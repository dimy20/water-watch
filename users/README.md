# Usuarios y permisos

Cada componente del sistema usa un usuario con los permisos mínimos necesarios para su función.

## Resumen

| Usuario | Permisos | PostgreSQL | MongoDB |
|---|---|---|---|
| `streamlit_user` | Solo lectura | SELECT | `read` |
| `etl_user` | Lectura + escritura | SELECT, INSERT, UPDATE | `find`, `insert`, `update` |
| `mig_user` | Solo DDL (sin datos) | CREATE, ALTER, DROP | — |
| `enzo_admin` | Administrador | ALL PRIVILEGES | `dbOwner` |
| `belen_admin` | Administrador | ALL PRIVILEGES | `dbOwner` |

---

## streamlit_user

**PostgreSQL**

```sql
CREATE USER streamlit_user WITH PASSWORD '<password>';

GRANT CONNECT ON DATABASE water_watch_test_db TO streamlit_user;
GRANT USAGE ON SCHEMA public TO streamlit_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO streamlit_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO streamlit_user;
```

**MongoDB**

```js
use water_watch_test_db

db.createUser({
  user: "streamlit_user",
  pwd: "<password>",
  roles: [{ role: "read", db: "water_watch_test_db" }]
})
```

---

## etl_user

**PostgreSQL**

```sql
CREATE USER etl_user WITH PASSWORD '<password>';

GRANT CONNECT ON DATABASE water_watch_test_db TO etl_user;
GRANT USAGE ON SCHEMA public TO etl_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE ON TABLES TO etl_user;
```

**MongoDB**

```js
db.createRole({
  role: "etl_read_insert_update",
  privileges: [{
    resource: { db: "grp05db", collection: "" },
    actions: ["find", "insert", "update"]
  }],
  roles: []
})

db.createUser({
  user: "etl_user",
  pwd: "<password>",
  roles: [{ role: "etl_read_insert_update", db: "grp05db" }]
})
```

---

## mig_user

Solo PostgreSQL. Puede alterar la estructura de las tablas (DDL) pero no leer ni escribir datos.

```sql
CREATE USER mig_user WITH PASSWORD '<password>';

GRANT CONNECT ON DATABASE water_watch_test_db TO mig_user;
GRANT USAGE, CREATE ON SCHEMA public TO mig_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO mig_user;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO mig_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES TO mig_user;
```

---

## Administradores

### enzo_admin

**PostgreSQL**

```sql
CREATE USER enzo_admin WITH PASSWORD '<password>';

GRANT ALL PRIVILEGES ON DATABASE water_watch_test_db TO enzo_admin;
GRANT ALL PRIVILEGES ON SCHEMA public TO enzo_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO enzo_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO enzo_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO enzo_admin;
```

**MongoDB**

```js
db.createUser({
  user: "enzo_admin",
  pwd: "<password>",
  roles: [{ role: "dbOwner", db: "grp05db" }]
})
```

### belen_admin

**PostgreSQL**

```sql
CREATE USER belen_admin WITH PASSWORD '<password>';

GRANT ALL PRIVILEGES ON DATABASE water_watch_test_db TO belen_admin;
GRANT ALL PRIVILEGES ON SCHEMA public TO belen_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO belen_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO belen_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO belen_admin;
```

**MongoDB**

```js
db.createUser({
  user: "belen_admin",
  pwd: "<password>",
  roles: [{ role: "dbOwner", db: "grp05db" }]
})
```
