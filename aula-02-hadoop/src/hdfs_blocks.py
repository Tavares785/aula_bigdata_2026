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
    # ESTUDO: dividimos o tamanho do arquivo pelo tamanho do bloco.
    # Ex: 300 MB / 128 MB = 2.34375 blocos
    # Como um bloco parcial ainda ocupa um bloco inteiro no HDFS,
    # usamos math.ceil() para arredondar SEMPRE para cima.
    # math.ceil(2.34375) -> 3
    # math.ceil(2.0)     -> 2
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
    # ESTUDO: o HDFS replica cada bloco N vezes entre DataNodes diferentes.
    # Isso garante que, se um nó cair, os dados ainda estejam disponíveis
    # em outros nós. O custo é que o espaço em disco é multiplicado.
    # Ex: 100 MB com fator 3 -> 100 * 3 = 300 MB usados no cluster total.
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
    # ESTUDO: Round-robin significa distribuir em ordem circular.
    # Bloco 1 -> datanode-1, bloco 2 -> datanode-2, bloco 3 -> datanode-3,
    # bloco 4 -> datanode-1 (volta ao início), e assim por diante.

    # Passo 1: cria o dicionário com uma lista vazia para cada datanode.
    # Ex: {"datanode-1": [], "datanode-2": [], "datanode-3": []}
    distribution = {f"datanode-{i}": [] for i in range(1, num_datanodes + 1)}

    # Passo 2: percorre cada bloco (numerados de 1 até num_blocks)
    for block_id in range(1, num_blocks + 1):
        # ESTUDO: o operador módulo (%) retorna o resto da divisão.
        # Usamos (block_id - 1) % num_datanodes para obter um índice de 0 a N-1,
        # e somamos 1 para obter o número do datanode (que começa em 1).
        # Ex com 3 datanodes:
        #   block_id=1: (1-1) % 3 = 0 -> datanode-1
        #   block_id=2: (2-1) % 3 = 1 -> datanode-2
        #   block_id=3: (3-1) % 3 = 2 -> datanode-3
        #   block_id=4: (4-1) % 3 = 0 -> datanode-1  (volta!)
        node_index = (block_id - 1) % num_datanodes + 1
        node_name = f"datanode-{node_index}"
        distribution[node_name].append(block_id)

    return distribution
