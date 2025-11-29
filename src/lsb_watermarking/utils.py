"""
Utility functions for LSB watermarking
"""
import os
import numpy as np


def string_to_binary(st):
    """ Convert string to binary string """
    return ''.join(format(ord(i), '08b') for i in st)


def binary_to_string(bi):
    """ Convert binary string to string """
    return ''.join(chr(int(byte, 2)) for byte in [bi[ii:ii+8] for ii in range(0, len(bi), 8)])


def get_num_bits(path, msg_type):
    """ Get the number of bits of the watermark from the text file """
    with open(path, 'r') as f:
        lines = [line.strip() for line in f]
    if msg_type == 'bit':
        return max([len(line) for line in lines]) if lines else 0
    else:
        return 8 * max([len(line) for line in lines]) if lines else 0


def load_messages(path, msg_type, N):
    """ Load messages from a file """
    with open(path, 'r') as f:
        lines = [line.strip() for line in f]
    
    if not lines:
        return np.array([])
    
    if msg_type == 'bit':
        num_bit = max([len(line) for line in lines])
        lines = [line + '0' * (num_bit - len(line)) for line in lines]
        msgs = [[int(i) == 1 for i in line] for line in lines]
    else:
        num_byte = max([len(line) for line in lines])
        lines = [line + ' ' * (num_byte - len(line)) for line in lines]
        msgs = [[int(i) == 1 for i in string_to_binary(line)] for line in lines]
    
    # Repeat messages if needed
    msgs = msgs * (N // len(msgs) + 1)
    return np.array(msgs[:N], dtype=bool)


def save_messages(msgs, path):
    """ Save messages to file """
    txt_msgs = [''.join(map(str, x.astype(int).tolist())) for x in msgs]
    txt_msgs = '\n'.join(txt_msgs)
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w') as f:
        f.write(txt_msgs)


def generate_messages(n, k):
    """
    Generate random messages.
    Args:
        n: Number of messages to generate
        k: length of the message in bits
    Returns:
        msgs: boolean array of size n x k
    """
    return np.random.rand(n, k) > 0.5

