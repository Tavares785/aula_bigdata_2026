"""
Aula 02 - HDFS (Hadoop Distributed File System)
Lab: Simule, em Python, como o HDFS divide arquivos em blocos e os
distribui entre os nós (DataNodes) de um cluster.

Isso NÃO substitui o HDFS real -- é um modelo simplificado para você
praticar, na prática, os cálculos que o NameNode faz por trás dos panos
sempre que um arquivo é gravado no HDFS.

Como testar localmente antes de enviar a PR:
    pip install -r requirements.txt
    pytest -v
"""

import math


def calculate_num_blocks(file_size_mb: float, block_size_mb: int = 128) -> int:
    """
    Calcule quantos blocos HDFS são necessários para armazenar um arquivo
    de `file_size_mb` megabytes, usando blocos de `block_size_mb` MB cada.

    O último bloco pode ficar parcialmente ocupado, mas conta como 1 bloco.
    Por isso, o resultado deve ser sempre arredondado para cima.

    Exemplos:
        calculate_num_blocks(256, block_size_mb=128) -> 2
        calculate_num_blocks(300, block_size_mb=128) -> 3
        calculate_num_blocks(1, block_size_mb=128) -> 1
    """

    return math.ceil(file_size_mb / block_size_mb)


def calculate_total_storage_with_replication(
    file_size_mb: float,
    replication_factor: int = 3
) -> float:
    """
    Calcule o espaço TOTAL em disco, em MB, ocupado no cluster
    considerando o fator de replicação.

    Exemplo:
        calculate_total_storage_with_replication(100) -> 300
        calculate_total_storage_with_replication(100, replication_factor=1) -> 100
    """

    return file_size_mb * replication_factor


def simulate_block_distribution(
    num_blocks: int,
    num_datanodes: int
) -> dict:
    """
    Simule a distribuição round-robin dos blocos entre os DataNodes.

    Os blocos são numerados de 1 até num_blocks.

    Exemplo com 6 blocos e 3 DataNodes:

        {
            "datanode-1": [1, 4],
            "datanode-2": [2, 5],
            "datanode-3": [3, 6]
        }
    """

    distribution = {}

    # Cria os DataNodes
    for datanode in range(1, num_datanodes + 1):
        distribution[f"datanode-{datanode}"] = []

    # Distribui os blocos em formato round-robin
    for block_id in range(1, num_blocks + 1):
        datanode_id = ((block_id - 1) % num_datanodes) + 1
        datanode_name = f"datanode-{datanode_id}"

        distribution[datanode_name].append(block_id)

    return distribution
