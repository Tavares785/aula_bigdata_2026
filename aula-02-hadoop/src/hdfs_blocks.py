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
    TODO 1:
    Calcule quantos blocos HDFS são necessários para armazenar um arquivo
    de `file_size_mb` megabytes, usando blocos de `block_size_mb` MB cada.

    Regra do HDFS: todo bloco (exceto possivelmente o último) tem o
    tamanho cheio; o último bloco pode ficar parcialmente ocupado, mas
    ainda assim conta como 1 bloco inteiro (ou seja: arredonde SEMPRE
    para cima).

    Exemplos:
        calculate_num_blocks(256, block_size_mb=128) -> 2
        calculate_num_blocks(300, block_size_mb=128) -> 3  (2 blocos cheios + 1 parcial)
        calculate_num_blocks(1,   block_size_mb=128) -> 1
    """
    return math.ceil(file_size_mb / block_size_mb)


def calculate_total_storage_with_replication(file_size_mb: float, replication_factor: int = 3) -> float:
    """
    TODO 2:
    Calcule o espaço TOTAL em disco (em MB) realmente ocupado no cluster
    para armazenar um arquivo de `file_size_mb` MB, considerando o fator
    de replicação (por padrão, o Hadoop replica cada bloco 3 vezes, para
    tolerância a falhas).

    Exemplo:
        calculate_total_storage_with_replication(100) -> 300
        calculate_total_storage_with_replication(100, replication_factor=1) -> 100
    """
    return file_size_mb * replication_factor


def simulate_block_distribution(num_blocks: int, num_datanodes: int) -> dict:
    """
    TODO 3:
    Simule a distribuição round-robin (sem replicação, apenas para
    simplificar o exercício) de `num_blocks` blocos -- numerados de 1 até
    num_blocks -- entre `num_datanodes` DataNodes, nomeados
    "datanode-1", "datanode-2", etc.

    Retorne um dicionário no formato:
        {nome_do_datanode: [lista_de_ids_de_blocos_naquele_node]}

    Exemplo com 6 blocos e 3 datanodes:
        {
          "datanode-1": [1, 4],
          "datanode-2": [2, 5],
          "datanode-3": [3, 6],
        }
    """
    distribution = {f"datanode-{i+1}": [] for i in range(num_datanodes)}
    
    for block_id in range(1, num_blocks + 1):
        datanode_index = (block_id - 1) % num_datanodes
        datanode_name = f"datanode-{datanode_index + 1}"
        distribution[datanode_name].append(block_id)
    
    return distribution
