-- agregar columa correo a usuarios
-- depends: 20260515_01_4pN72-nueva-tabla-usuarios
ALTER TABLE usuarios
ADD COLUMN email VARCHAR(255) NOT NULL;
