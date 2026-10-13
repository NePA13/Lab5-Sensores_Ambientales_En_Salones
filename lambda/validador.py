import base64
import json
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import boto3

tabla = boto3.resource("dynamodb").Table(os.environ["TABLA"])
sqs = boto3.client("sqs")
SQS_URL = os.environ["SQS_URL"]

CAMPOS = ["sensorId", "aula", "edificio", "timestamp", "temperatura", "humedad", "co2"]
RANGOS = {"temperatura": (-10, 60), "humedad": (0, 100), "co2": (400, 5000)}


def validar(d):
    errores = [f"falta {c}" for c in CAMPOS if d.get(c) in (None, "")]
    if errores:
        return errores

    for campo, (minimo, maximo) in RANGOS.items():
        v = d[campo]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            errores.append(f"{campo} no es numero")
        elif not minimo <= v <= maximo:
            errores.append(f"{campo} fuera de rango ({v})")

    try:
        ts = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00"))
        ahora = datetime.now(timezone.utc)
        if ts.tzinfo is None:
            errores.append("timestamp sin zona horaria")
        elif ts > ahora + timedelta(minutes=1):
            errores.append("timestamp en el futuro")
        elif ts < ahora - timedelta(hours=24):
            errores.append("timestamp muy viejo")
    except (ValueError, AttributeError):
        errores.append("timestamp invalido")

    return errores


def calcular_estado(co2):
    if co2 < 1000:
        return "ok"
    if co2 <= 1500:
        return "ventilar"
    return "critico"


def mandar_a_sqs(crudo, errores):
    sqs.send_message(
        QueueUrl=SQS_URL,
        MessageBody=json.dumps({
            "original": crudo,
            "errores": errores,
            "recibido": datetime.now(timezone.utc).isoformat(),
        }),
    )


def lambda_handler(event, context):
    validos = rechazados = 0

    for record in event["Records"]:
        crudo = base64.b64decode(record["kinesis"]["data"]).decode("utf-8", errors="replace")

        try:
            d = json.loads(crudo)
            if not isinstance(d, dict):
                raise ValueError
        except ValueError:
            mandar_a_sqs(crudo, ["JSON invalido"])
            rechazados += 1
            continue

        errores = validar(d)
        if errores:
            mandar_a_sqs(crudo, errores)
            rechazados += 1
            continue

        item = {c: d[c] for c in CAMPOS}
        item["estado"] = calcular_estado(d["co2"])
        # DynamoDB no acepta float, hay que pasarlo a Decimal
        item = json.loads(json.dumps(item), parse_float=Decimal)
        tabla.put_item(Item=item)
        validos += 1

    print(f"validos={validos} rechazados={rechazados}")
    return {"validos": validos, "rechazados": rechazados}
