import json
import os
import random
import time
from datetime import datetime, timezone

import boto3

STREAM = os.environ.get("STREAM_NAME", "aulas-sensores-stream")
INTERVALO = float(os.environ.get("INTERVALO", "5"))
TASA_ERROR = float(os.environ.get("TASA_ERROR", "0.1"))

kinesis = boto3.client("kinesis", region_name=os.environ.get("AWS_REGION", "us-east-1"))

AULAS = ["T-201", "T-202", "T-305", "D-101", "D-204", "A-110"]

# Estado actual de cada salón, para que los valores cambien poco a poco
estado = {
    a: {
        "temperatura": random.uniform(21, 25),
        "humedad": random.uniform(40, 55),
        "co2": random.uniform(450, 700),
    }
    for a in AULAS
}


def ahora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def limitar(v, minimo, maximo):
    return max(minimo, min(v, maximo))


def siguiente_lectura(aula):
    e = estado[aula]
    e["temperatura"] = limitar(e["temperatura"] + random.uniform(-0.3, 0.4), 18, 32)
    e["humedad"] = limitar(e["humedad"] + random.uniform(-1, 1), 30, 70)
    e["co2"] = limitar(e["co2"] + random.uniform(-40, 90), 420, 2200)

    # Si el CO2 está muy alto, a veces "abren la ventana"
    if e["co2"] > 1600 and random.random() < 0.2:
        e["co2"] = random.uniform(500, 700)

    return {
        "sensorId": aula.replace("-", "") + "-s1",
        "aula": aula,
        "edificio": aula.split("-")[0],
        "timestamp": ahora(),
        "temperatura": round(e["temperatura"], 1),
        "humedad": round(e["humedad"], 1),
        "co2": int(e["co2"]),
    }


def descomponer(lectura):
    """Mete un error a propósito para probar la Lambda."""
    tipo = random.choice(["falta_campo", "fuera_rango", "texto", "timestamp", "json"])
    if tipo == "falta_campo":
        lectura.pop(random.choice(["co2", "humedad", "temperatura"]))
    elif tipo == "fuera_rango":
        lectura["temperatura"] = random.choice([-40, 99.9])
    elif tipo == "texto":
        lectura["co2"] = "error"
    elif tipo == "timestamp":
        lectura["timestamp"] = "ayer"
    elif tipo == "json":
        return '{"aula": "' + lectura["aula"] + '", "co2": '  # JSON cortado
    return json.dumps(lectura)


def main():
    print(f"Mandando a {STREAM} cada {INTERVALO}s (errores: {TASA_ERROR:.0%})", flush=True)
    while True:
        registros = []
        for aula in AULAS:
            lectura = siguiente_lectura(aula)
            if random.random() < TASA_ERROR:
                data = descomponer(lectura)
            else:
                data = json.dumps(lectura)
            registros.append({"Data": data.encode("utf-8"), "PartitionKey": aula})

        resp = kinesis.put_records(StreamName=STREAM, Records=registros)
        print(f"{ahora()} enviados={len(registros)} fallidos={resp['FailedRecordCount']}", flush=True)
        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
