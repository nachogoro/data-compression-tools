#!/usr/bin/env python3
import argparse
import re
from tabulate import tabulate
import sys


def compress(input_str: str, explain: bool = False):
    """
    Compress `input_str` using LZ78, returning two things:
    1) The compression tokens as a single string (e.g. '(0,S)(0,H)...(x,<EOF>)').
    2) A table (list of rows) describing each step, if needed for explanation.
    """
    if explain:
        msg = (
            "LZ78 starts with a dictionary initialized with a single entry: "
            "the empty string, with index 0.\n"
            "It then consumes the entry by taking the longest prefix already "
            "in the dictionary plus the next symbol.\n"
            "It outputs a pair (index, symbol), where:\n"
            "\t- index is the index in the dictionary for the longest already-seen prefix.\n"
            "\t- symbol is the symbol following it.\n"
            "After emitting each pair, it adds the string they represent to "
            "the dictionary, using the next available index")
        print(msg)

    # Replace spaces with underscores for internal processing
    # (so that tokens can store them unambiguously).
    processed = input_str.replace(' ', '_')

    # Dictionary mapping substring -> index
    dictionary = {'': 0}
    current_string = ''

    # We'll gather rows: [Step, Symbol, Prev, Concat, Concat in dict?, Prev index, Addition, Output]
    table_rows = []

    # We also keep track of the final list of tokens to output
    tokens = []

    step = 1
    for symbol in processed:
        concatenated = current_string + symbol
        prev = current_string
        prev_index = dictionary[prev]
        in_dict = concatenated in dictionary

        if in_dict:
            # No output token here, continue building 'current_string'
            output = '--'
            addition = '--'
            current_string = concatenated
        else:
            # We must create a new dictionary entry
            output = f'({prev_index},{symbol})'
            tokens.append(output)
            dictionary[concatenated] = len(dictionary)
            addition = f'{concatenated} => {dictionary[concatenated]}'
            current_string = ''

        table_rows.append([
            step,
            symbol,
            prev,
            concatenated,
            in_dict,
            prev_index,
            addition,
            output
        ])
        step += 1

    final_token = f'({dictionary[current_string]},<EOF>)'
    tokens.append(final_token)

    # Add a final row to represent the "end"
    table_rows.append([
        step,
        '<EOF>',
        current_string,
        '--',
        '--',
        dictionary[current_string],
        '--',
        final_token
    ])

    # Join tokens into a single string for easy decompression input
    compressed_str = ''.join(tokens)
    return compressed_str, table_rows


def decompress(compressed_str: str, explain: bool = False):
    """
    Decompress a string of tokens of the form
    '(index, symbol)(index, symbol)...(index,<EOF>)' produced by `compress`.
    Returns two things:
    1) The decompressed string.
    2) A table (list of rows) describing each step, if needed for explanation.
    """

    if explain:
        msg = (
            "LZ78 starts with a dictionary initialized with a single entry: "
            "the empty string, with index 0.\n"
            "It then consumes the entry pair by pair.\n"
            "A pair is of the form (index, symbol), where:\n"
            "\t- index is the index in the dictionary for an already-seen string.\n"
            "\t- symbol is the symbol following it.\n"
            "It concatenates the string represented by index with symbol to "
            "obtain the string representation of that pair.\n"
            "After processing each pair, it adds the string it represents to "
            "the dictionary, using the next available index")
        print(msg)

    # We will track each token and the partial output
    table_rows = []
    # Dictionary mapping index -> string
    dictionary = {0: ""}
    output_pieces = []
    current_index = 0

    # Parse tokens using a regex
    #   each token is of the form (someInt, something)
    #   note that "something" could be <EOF>, a letter, or underscore, etc.
    #   We'll allow any non-`)` sequence (lazy approach).
    pattern = r"\((\d+),([^)]*)\)"
    tokens = re.findall(pattern, compressed_str)

    step = 1
    for i, (idx_str, symbol) in enumerate(tokens):
        idx = int(idx_str)
        if symbol == "<EOF>":
            # If we encounter EOF, we stop reading further tokens
            table_rows.append([
                step,
                f"({idx},{symbol})",
                dictionary.get(idx, ""),
                "--",
                "EOF reached",
                f"{dictionary.get(idx, '')}"
            ])

            output_pieces.append(dictionary.get(idx, ""))
            break

        # The new string is dictionary[idx] + the symbol
        prefix = dictionary[idx]
        new_string = prefix + symbol
        current_index += 1
        dictionary[current_index] = new_string

        # For final output, we accumulate
        output_pieces.append(new_string)

        table_rows.append([
            step,
            f"({idx},{symbol})",
            prefix,
            symbol,
            f"Index {current_index} => '{new_string}'",
            new_string
        ])
        step += 1

    # Join them, then replace underscores back with spaces
    decompressed_str = ''.join(output_pieces).replace('_', ' ')
    return decompressed_str, table_rows


def main():
    parser = argparse.ArgumentParser(
        description="Compress or decompress text with LZ78."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--compress", action="store_true", help="Compress the input")
    group.add_argument("--decompress", action="store_true", help="Decompress the input")

    parser.add_argument("--file", type=str, help="Read input from FILE instead of the command line")
    parser.add_argument("--explain", action="store_true", help="Print explanation of the process")

    parser.add_argument("input_string", nargs="?",
                        help="String to compress/decompress (if --file not used)")

    args = parser.parse_args()

    # Figure out the actual input
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                data = f.read().rstrip('\n')
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)
    else:
        if not args.input_string:
            print("Error: No input provided (either use --file or pass a string).", file=sys.stderr)
            sys.exit(1)
        data = args.input_string

    if args.compress:
        compressed_str, table_rows = compress(data, explain=args.explain)
        if args.explain:
            headers = ["Step", "Symbol", "Prev", "Concatenation", "Concat in dict?", "Prev index",
                       "Addition", "Output"]
            table = tabulate(table_rows, headers=headers, tablefmt="grid")
            print(table)
            print("\nCompressed output:")
        print(compressed_str)

    elif args.decompress:
        decompressed_str, table_rows = decompress(data, explain=args.explain)
        if args.explain:
            headers = ["Step", "Token", "Prefix from dict[idx]", "Symbol", "Dictionary Update",
                       "Output so far"]
            table = tabulate(table_rows, headers=headers, tablefmt="grid")
            print(table)
            print("\nDecompressed output:")
        print(decompressed_str)


if __name__ == "__main__":
    main()
