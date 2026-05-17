-- agregando precio a ropas
-- depends: 20260515_03_v1mQH-crear-tabla-ropas
-- adasdasd

ALTER TABLE ropas
ADD column precio int check (precio >= 0 AND precio <= 1100);
