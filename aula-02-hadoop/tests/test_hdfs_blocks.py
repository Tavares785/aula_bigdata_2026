import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hdfs_blocks import (
    calculate_num_blocks,
    calculate_total_storage_with_replication,
    simulate_block_distribution,
)


def test_calculate_num_blocks_exact_multiple():
    assert calculate_num_blocks(256, block_size_mb=128) == 2


def test_calculate_num_blocks_rounds_up():
    assert calculate_num_blocks(300, block_size_mb=128) == 3


def test_calculate_num_blocks_small_file_still_uses_one_block():
    assert calculate_num_blocks(1, block_size_mb=128) == 1


def test_calculate_num_blocks_default_block_size():
    assert calculate_num_blocks(128) == 1
    assert calculate_num_blocks(129) == 2


def test_replication_storage_default_factor():
    assert calculate_total_storage_with_replication(100) == 300


def test_replication_storage_custom_factor():
    assert calculate_total_storage_with_replication(100, replication_factor=1) == 100


def test_block_distribution_round_robin():
    dist = simulate_block_distribution(num_blocks=6, num_datanodes=3)
    assert set(dist.keys()) == {"datanode-1", "datanode-2", "datanode-3"}
    assert dist["datanode-1"] == [1, 4]
    assert dist["datanode-2"] == [2, 5]
    assert dist["datanode-3"] == [3, 6]


def test_block_distribution_uneven_blocks():
    dist = simulate_block_distribution(num_blocks=5, num_datanodes=2)
    assert dist["datanode-1"] == [1, 3, 5]
    assert dist["datanode-2"] == [2, 4]
