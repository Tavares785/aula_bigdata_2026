"""
Aula 03 - Apache Kafka e Spark Streaming
Lab (parte 1/2): Parsing e validacao de mensagens vindas de um topico
Kafka.

Contexto
--------
Em um pipeline real, um Kafka Consumer recebe mensagens em formato de
texto/bytes (o "value" da mensagem) e precisa:
  1. Decodificar/parsear o conteudo (geralmente JSON)
  2. Validar se a mensagem tem os campos esperados antes de processa-la
Este arquivo foca exatamente nessa logica -- a MESMA logica que voce
colocaria dentro de um Kafka Consumer real ou de um mapper de Spark
Streaming, so que aqui testada de forma isolada (sem precisar de um
broker Kafka rodando).

Como testar localmente antes de enviar a PR:
    pip install -r requirements.txt
    pytest -v
"""
import json

# Campos que toda mensagem de evento precisa ter para ser considerada
# valida neste pipeline.
REQUIRED_FIELDS = {"event_id", "event_time", "category", "amount"}


def parse_kafka_message(raw_value: str) -> dict:
  
  
  # 1 e 2: Tenta fazer o parse e trata JSON malformatado
    try:
        data = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("Mensagem nao e um JSON valido")

  # 3: Garante que o JSON parseado seja um objeto/dicionário (e não número, string ou lista solta)
    if not isinstance(data, dict):
        raise ValueError("Mensagem JSON deve representar um objeto")

  # 4: Valida se todos os campos obrigatórios estão presentes
    faltantes = set(REQUIRED_FIELDS) - set(data.keys())
    if faltantes:
        raise ValueError(f"Campos obrigatorios ausentes: {sorted(faltantes)}")

    # 5: Retorna o dicionário pronto para uso
    return data

def is_valid_event(event: dict) -> bool:
    
    # Regra 1: Valida se todos os campos de REQUIRED_FIELDS estao presentes
    if not all(field in event for field in REQUIRED_FIELDS):
        return False

    amount = event.get("amount")

    # Regra 2: Valida se 'amount' e int ou float (evitando que bool passe como int)
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        return False

    # Regra 3: Valida se 'amount' e maior ou igual a zero
    if amount < 0:
        return False

    return True

def filter_valid_events(events: list[dict]) -> list[dict]:

  return [event for event in events if is_valid_event(event)]
   
