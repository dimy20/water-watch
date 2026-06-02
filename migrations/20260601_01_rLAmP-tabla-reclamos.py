from yoyo import step

__depends__ = {}

steps = [
    step(
        """--sql
        CREATE TABLE ReclamosOSE (
            reclamo_id UUID PRIMARY KEY,
            departamento_id UUID NOT NULL,

            tipo_reclamo VARCHAR(100) NOT NULL,
            region VARCHAR(100) NOT NULL,

            fecha_inicio TIMESTAMP NOT NULL,
            fecha_fin TIMESTAMP NOT NULL,

            CHECK (fecha_fin >= fecha_inicio)
    );
        """
    )
]