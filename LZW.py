#!/usr/bin/env python3
import argparse
import sys
import re
from tabulate import tabulate

def lzw_compress(input_str: str, explain: bool=False):
    """
    Compress `input_str` (with spaces replaced by underscores) using LZW.

    Returns:
      codes (list of int): The compressed numeric codes.
      table_rows (list of lists): Step-by-step info for explanation (if needed).
    """
    if explain:
        msg = (
            "LZW starts with a dictionary initialized with all single-symbol strings.\n"
            "It then consumes the entry by taking the longest prefix already "
            "in the dictionary.\n"
            "It outputs the longest prefix, and adds the prefix concatenated "
            "with the next symbol of the string to the dictionary.\n"
            )
        print(msg)

    # Replace paces with underscores for internal representation.
    processed = input_str.replace(' ', '_')

    # Initialize dictionary with single-character strings
    # 'A'..'Z' => 1..26
    # '_' => 27
    dictionary = {}
    for c in range(ord('A'), ord('Z')+1):
        dictionary[chr(c)] = len(dictionary)+1
    dictionary['_'] = len(dictionary)+1

    # We will build LZW codes in `output_codes`.
    # We also collect table rows
    output_codes = []
    table_rows = []

    # Current recognized sequence
    word = ""
    step = 0

    # For the table, let's store:
    # [Step, Symbol, Word (old), Concat,
    #  Concat in dict, Word(new), Output, Addition]
    # We'll add an initial row to mirror your example
    if explain:
        table_rows.append([0, '--', '--', '--', '--', '""', '--', '--'])

    for step, symbol in enumerate(processed, 1):
        old_word = word
        concatenated = old_word + symbol
        in_dict = concatenated in dictionary
        if in_dict:
            # If the concatenated string is in the dictionary, keep building.
            output = "--"
            addition = "--"
            word = concatenated
        else:
            # Output the code for 'old_word'
            output = dictionary[old_word]
            dictionary[concatenated] = len(dictionary)+1
            addition = f"{concatenated} => {dictionary[concatenated]}"
            # Start `word` again from the current symbol
            word = symbol
            # Store the code
            output_codes.append(output)

        table_rows.append([
            step,
            symbol,
            old_word,
            concatenated,
            in_dict,
            word,
            output,
            addition
        ])

    # Output the last string
    final_code = dictionary[word]
    output_codes.append(final_code)
    table_rows.append([
        step+1,
        "<EOF>",
        word,
        "--",
        "--",
        "--",
        final_code,
        "--"
    ])

    return output_codes, table_rows


import re

def lzw_decompress(code_str: str, explain: bool=False):
    """
    Decompress a series of numeric codes (string) produced by `lzw_compress`.

    Example of `code_str`: "3,5,10,27"
    or space-separated "3 5 10 27" etc.

    Returns:
      decompressed (str): The decompressed string with underscores replaced by spaces.
      table_rows (list of lists): Step-by-step info for explanation (if needed).
    """
    if explain:
        msg = (
            "LZW decompression begins with a dictionary of single-symbol strings.\n"
            "It reads each code and looks it up in the dictionary to obtain the corresponding string:\n"
            "\t- If the code is in the dictionary, the string is the one corresponding to it.\n"
            "\t- If the code is NOT in the dictionary, the string is the last decoded string + its own fist char.\n"
            "After outputting the decoded string,a new dictionary entry is added:\n"
            "It consists of the previous decoded string concatenated with the first "
            "character of the current decoded string.\n"
        )
        print(msg)

    # Parse the code string, splitting on comma and/or whitespace
    # This handles both comma-separated or space-separated codes.
    code_values = re.split(r'[\s,]+', code_str.strip())
    # Filter out possible empty strings if there's trailing commas/spaces
    code_values = [cv for cv in code_values if cv]

    # Convert to int
    codes = list(map(int, code_values))

    # Build the initial dictionary (inverse of compress)
    # Index 1..26 -> 'A'..'Z', 27 -> '_'
    dictionary = {}
    for c in range(ord('A'), ord('Z') + 1):
        dictionary[len(dictionary) + 1] = chr(c)
    dictionary[len(dictionary) + 1] = '_'

    # We'll build the output characters in `decompressed_pieces`.
    decompressed_pieces = []

    # For explanation, we store rows as:
    # [Step, Code, Dictionary Entry, Dictionary Addition, Output so far]
    table_rows = []

    if not codes:
        return "", table_rows

    # LZW decompression algorithm
    # 1) The first code is just looked up in the dictionary.
    old_code = codes[0]
    old_string = dictionary[old_code]
    decompressed_pieces.append(old_string)

    table_rows.append([
        1,
        old_code,
        old_string,
        "--",
        old_string
    ])

    for step, c in enumerate(codes[1:], 2):
        if c in dictionary:
            explanation = current_string = dictionary[c]
        else:
            # If code 'c' is not yet in the dictionary, it must be
            # old_string + the first character of old_string.
            current_string = old_string + old_string[0]
            explanation = f"{old_string} + {old_string[0]}"

        decompressed_pieces.append(current_string)

        # Build new entry in the dictionary:
        # dictionary[next_code_idx] = old_string + first char of current_string
        new_entry = old_string + current_string[0]
        dictionary[len(dictionary) + 1] = new_entry
        added_info = f"{len(dictionary)} => '{new_entry}'"

        so_far = ''.join(decompressed_pieces)
        table_rows.append([
            step,
            c,
            explanation,
            added_info,
            so_far
        ])

        old_string = current_string

    # Join all pieces, then replace underscores with spaces
    decompressed = ''.join(decompressed_pieces).replace('_', ' ')
    return decompressed, table_rows



def main():
    parser = argparse.ArgumentParser(description="Compress or decompress text with LZW.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--compress", action="store_true", help="Compress the input")
    group.add_argument("--decompress", action="store_true", help="Decompress the input")

    parser.add_argument("--file", type=str, help="Read input from FILE instead of the command line")
    parser.add_argument("--explain", action="store_true", help="Print explanation of the process")
    # Positional argument for the string or codes
    parser.add_argument("input_string", nargs="?", help="String or code list to process (if --file not used)")

    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                data = f.read().rstrip('\n')
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)
    else:
        if not args.input_string:
            print("Error: No input provided (either use --file or pass a string/codes).", file=sys.stderr)
            sys.exit(1)
        data = args.input_string

    if args.compress:
        codes, table_rows = lzw_compress(data, explain=args.explain)
        if args.explain:
            headers = ["Step", "Symbol", "Word (old)", "Concat",
                       "Concat in dict", "Word(new)", "Output", "Addition"]
            print(tabulate(table_rows, headers=headers, tablefmt="grid"))
            print("\nCompressed output (list of codes):")
        # Print codes as comma-separated by default
        print(",".join(str(c) for c in codes))

    elif args.decompress:
        decompressed, table_rows = lzw_decompress(data, explain=args.explain)
        if args.explain:
            headers = ["Step", "Code", "Entry", "Dictionary Addition", "Output so far"]
            print(tabulate(table_rows, headers=headers, tablefmt="grid"))
            print("\nDecompressed output:")
        print(decompressed)


if __name__ == "__main__":
    main()

