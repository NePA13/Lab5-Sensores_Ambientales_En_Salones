import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from flask import Flask, jsonify, request, send_from_directory

REGION = os.environ.get("AWS_REGION", "us-east-1")
TABLA = os.environ.get("TABLA", "lecturas-aulas")
SQS_URL = os.environ["SQS_URL"]
AULAS = os.environ.get("AULAS", "T-201,T-202,T-305,D-101,D-204,A-110").split(",")

tabla = boto3.resource("dynamodb", region_name=REGION).Table(TABLA)
sqs = boto3.client("sqs", region_name=REGION)
app = Flask(__name__, static_folder="static", static_url_path="")


def limpiar(item):
    # DynamoDB regresa Decimal, y JSON necesita float
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in item.items()}


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/ultimas")
def ultimas():
    """Última lectura de cada salón."""
    datos = []
    for aula in AULAS:
        r = tabla.query(
            KeyConditionExpression=Key("aula").eq(aula),
            ScanIndexForward=False,  # más reciente primero
            Limit=1,
        )
        if r["Items"]:
            datos.append(limpiar(r["Items"][0]))
    return jsonify(datos)


@app.get("/api/historial")
def historial():
    """Lecturas de un salón en los últimos N minutos."""
    aula = request.args.get("aula", AULAS[0])
    minutos = min(int(request.args.get("minutos", 30)), 1440)
    desde = (datetime.now(timezone.utc) - timedelta(minutes=minutos)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = tabla.query(KeyConditionExpression=Key("aula").eq(aula) & Key("timestamp").gte(desde))
    return jsonify([limpiar(i) for i in r["Items"]])


@app.get("/api/rechazados")
def rechazados():
    """Total de mensajes en SQS y algunos de ejemplo (sin borrarlos)."""
    attrs = sqs.get_queue_attributes(
        QueueUrl=SQS_URL, AttributeNames=["ApproximateNumberOfMessages"]
    )
    r = sqs.receive_message(QueueUrl=SQS_URL, MaxNumberOfMessages=10, VisibilityTimeout=0)
    mensajes = [json.loads(m["Body"]) for m in r.get("Messages", [])]
    return jsonify({
        "total": int(attrs["Attributes"]["ApproximateNumberOfMessages"]),
        "ultimos": mensajes,
    })
