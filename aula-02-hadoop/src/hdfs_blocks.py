import math


def calculate_num_blocks(file_size_mb: float, block_size_mb: int = 128) -> int:
    return math.ceil(file_size_mb / block_size_mb)


def calculate_total_storage_with_replication(
    file_size_mb: float, replication_factor: int = 3
) -> float:
    return file_size_mb * replication_factor


def simulate_block_distribution(num_blocks: int, num_datanodes: int) -> dict:
    distribution = {
        f"datanode-{i}": []
        for i in range(1, num_datanodes + 1)
    }

    for block_id in range(1, num_blocks + 1):
        datanode_index = (block_id - 1) % num_datanodes
        datanode_name = f"datanode-{datanode_index + 1}"
        distribution[datanode_name].append(block_id)

    return distribution