"""
Aula 03 - Apache Kafka e Spark Streaming
Lab (parte 1/2): Parsing e validacao de mensagens vindas de um topico
Kafka.
"""
import json

# Campos que toda mensagem de evento precisa ter para ser considerada
# valida neste pipeline.
REQUIRED_FIELDS = {"event_id", "event_time", "category", "amount"}


def parse_kafka_message(raw_value):
    """
    Recebe o value de uma mensagem Kafka e faz o parse/validacao basica.
    """
    try:
        event = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("Mensagem nao e um JSON valido")

    if not isinstance(event, dict):
        raise ValueError("Mensagem JSON deve representar um objeto")

    faltantes = REQUIRED_FIELDS - event.keys()

    if faltantes:
        raise ValueError(f"Campos obrigatorios ausentes: {sorted(faltantes)}")

    return event


def is_valid_event(event):
    """
    Retorna True se o evento possui todos os campos obrigatorios e
    amount e um numero maior ou igual a zero.
    """
    if not REQUIRED_FIELDS.issubset(event.keys()):
        return False

    amount = event["amount"]

    if not isinstance(amount, (int, float)):
        return False

    if amount < 0:
        return False

    return True


def filter_valid_events(events):
    """
    Retorna somente os eventos validos.
    """
    return [event for event in events if is_valid_event(event)]