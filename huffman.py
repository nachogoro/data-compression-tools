#!/usr/bin/env python3

import argparse
import sys
from math import log2, ceil
from collections import Counter, namedtuple
import heapq
from anytree import Node, RenderTree

def compute_entropy(probabilities):
    """
    Given a dict {symbol: probability}, compute the Shannon entropy:
      H(X) = -Σ p(x) log2(p(x))
    """
    entropy = 0.0
    for p in probabilities.values():
        if p > 0:
            entropy -= p * log2(p)
    return entropy

import heapq
from collections import namedtuple
from anytree import Node, RenderTree

def build_huffman_code(freq_table, explain=False):
    """
    Build a static Huffman code from a frequency table {symbol: count}.
    Returns:
      - codes: dict {symbol: binary_code_string}
      - avg_length: the average code length (sum of p_i * length(code_i))
      - probabilities: dict {symbol: p_i}, i.e. relative frequencies
      - huffman_tree: root node of the Huffman tree (for visualization)
    """

    if explain:
        msg = (
            "To build a Huffman code for a message, one needs to compute the "
            "frequency of appearance of each symbol.\n"
            "We then construct a tree using the following algorithm:\n"
            "\t- Treat all symbols as leaf nodes in a tree.\n"
            "\t- Each node has a weight: the frequency of that symbol.\n"
            "\t- While there are more than one node without a parent:\n"
            "\t\t- Make the two least nodes with the lowest weight the children of a new node.\n"
            "\t\t  Said node will have the combined weight of its children.\n"
            "At the end, we will have a single code tree.\n"
            "The path from the root to each symbol (leaf node) is the code for that symbol.\n"
            "\n"
            "Note that the tree will have the following properties:\n"
            "\t- All symbols are leaf nodes.\n"
            "\t- All intermediate nodes have exactly two children.\n"
            "\n"
            "Note that the code will have the following properties:\n"
            "\t- Given two symbols Si and Sj with frequencies Pi and Pj and code lengths Li and Lj:\n"
            "\t\tPi >= Pj --> Li <= Lj"
        )
        print(msg)

    # Compute probabilities
    total_count = sum(freq_table.values())
    probabilities = {sym: freq / total_count for sym, freq in freq_table.items()}

    # Edge case: if only one symbol, assign code "0"
    if len(freq_table) == 1:
        sym = next(iter(freq_table))
        return {sym: "0"}, 0.0, probabilities, Node(sym)

    # Min-heap of (count, unique_id, tree_node)
    heap = []
    unique_id = 0

    # Initialize heap with leaf nodes
    for sym, count in freq_table.items():
        node = Node(sym)  # Leaf node
        heapq.heappush(heap, (count, unique_id, node))
        unique_id += 1

    # Build Huffman tree
    while len(heap) > 1:
        count1, _, node1 = heapq.heappop(heap)
        count2, _, node2 = heapq.heappop(heap)

        merged_node = Node(f"{node1.name}+{node2.name}", children=[node1, node2])
        merged_count = count1 + count2
        heapq.heappush(heap, (merged_count, unique_id, merged_node))
        unique_id += 1

    # Extract root of Huffman tree
    [(_, _, root)] = heap

    # Generate Huffman codes
    codes = {}

    def traverse(node, prefix=""):
        if not node.children:  # Leaf node
            codes[node.name] = prefix
            return
        if node.children:
            traverse(node.children[0], prefix + "0")
            traverse(node.children[1], prefix + "1")

    traverse(root)

    # Compute average code length
    avg_length = sum(probabilities[sym] * len(codes[sym]) for sym in codes)

    return codes, avg_length, probabilities, root


def main():
    parser = argparse.ArgumentParser(
        description="Generate a static Huffman code for each symbol in a string."
    )
    parser.add_argument("input_string",
                        help="The input string from which to build a Huffman code.")
    parser.add_argument("--explain", action="store_true",
                        help="If set, explain the process (frequencies, probabilities, code table).")
    args = parser.parse_args()

    text = args.input_string.replace(' ', '_')
    if not text:
        print("Error: empty input string.", file=sys.stderr)
        sys.exit(1)

    # 1. Count frequencies
    freq_table = Counter(text)

    # 2. Build Huffman code (and possibly print explanation)
    codes, avg_length, probabilities, huffman_tree = build_huffman_code(freq_table, explain=args.explain)

    # 3. Compute entropy
    entropy = compute_entropy(probabilities)

    # 4. Print results
    sorted_symbols = sorted(freq_table.keys(), key=lambda s: (-freq_table[s], len(codes[s]), codes[s]))

    if args.explain:
        print(f'\n{text}')
        # Print ASCII tree representation
        print("\nHuffman Tree Representation:")
        for pre, _, node in RenderTree(huffman_tree):
            print(f"{pre}{node.name}")

        print("\nSymbol  Frequency  Probability     Huffman Code")
        for sym in sorted_symbols:
            print(f"{repr(sym):<7} {freq_table[sym]:<10} {probabilities[sym]:<15.6g} {codes[sym]}")
        print(f"\nEntropy of distribution: {entropy:.4f} bits/symbol")
        print(f"Average code length:     {avg_length:.4f} bits/symbol")
    else:
        # Minimal output: just show the code table, entropy, and average length.
        for sym in sorted_symbols:
            print(f"{repr(sym)} => {codes[sym]}")
        print()
        print(f"Entropy={entropy:.4f} bits/symbol, AvgCodeLen={avg_length:.4f} bits/symbol")

if __name__ == "__main__":
    main()
