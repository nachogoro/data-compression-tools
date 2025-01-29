#!/usr/bin/env python3
import argparse
import sys
import math
from tabulate import tabulate


def minimal_decimal_str(x, max_digits=12):
    """
    Convert float 'x' to a string with up to 'max_digits' significant digits,
    stripping trailing zeros after the decimal point.
    """
    s = format(x, f".{max_digits}g")  # e.g., up to 12 significant digits
    if '.' in s:
        s = s.rstrip('0').rstrip('.')  # remove trailing zeros and trailing '.'
    return s


def parse_frequencies(freq_str):
    """
    Parse a string like "A:0.2,B:0.3,C:0.5" into a dictionary:
    { 'A': 0.2, 'B': 0.3, 'C': 0.5 }
    """
    # Split by commas
    parts = freq_str.split(',')
    probabilities = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Each part is "Symbol:Freq"
        try:
            symbol, freq_s = part.split(':')
            symbol = symbol.strip()
            freq = float(freq_s.strip())
            probabilities[symbol] = freq
        except ValueError:
            print(f"Error: Cannot parse frequency component '{part}'. "
                  f"Expected format 'Symbol:Freq'.", file=sys.stderr)
            sys.exit(1)

    # Check if sum(probabilities.values()) ~ 1.0
    if not math.isclose(sum(probabilities.values()), 1.0):#, 1e-5):
        return None

    return probabilities


def build_cdf(probabilities):
    """
    Build a dictionary of cumulative distribution:
    cdf[sym] = sum of all p(x) for x < sym (sorted by symbol).
    cdf_next[sym] = cdf[sym] + probabilities[sym].
    Returns (cdf, cdf_next, sorted_symbols).
    """
    sorted_syms = sorted(probabilities.keys())
    cdf = {}
    running_sum = 0.0
    for s in sorted_syms:
        cdf[s] = running_sum
        running_sum += probabilities[s]
    cdf_next = {s: cdf[s] + probabilities[s] for s in sorted_syms}
    return cdf, cdf_next, sorted_syms


def arithmetic_encode(probabilities, message, explain=False):
    """
    Perform arithmetic encoding on 'message' using the specified dictionary
    'probabilities' {symbol: p}. Returns:
      - table_rows (for explanation)
      - final interval (L, H)
    """
    cdf, cdf_next, sorted_syms = build_cdf(probabilities)

    L = 0.0
    H = 1.0
    table_rows = [[0, '--', '--', '--', '0.0', '1.0']]

    for i, sym in enumerate(message, start=1):
        interval_width = H - L

        # Sub-interval for this symbol
        sym_low = cdf[sym]
        sym_high = cdf_next[sym]

        newL = L + interval_width * sym_low
        newH = L + interval_width * sym_high

        interval_width_str = minimal_decimal_str(interval_width)
        L_str = minimal_decimal_str(L)
        H_str = minimal_decimal_str(H)
        newL_str = minimal_decimal_str(newL)
        newH_str = minimal_decimal_str(newH)
        table_rows.append([
            i,
            sym,
            f"[{minimal_decimal_str(sym_low)}, {minimal_decimal_str(sym_high)})",
            interval_width_str,
            f"{L_str} + {interval_width_str} * {minimal_decimal_str(sym_low)} = {newL_str}",
            f"{L_str} + {interval_width_str} * {minimal_decimal_str(sym_high)} = {newH_str}",
        ])

        L, H = newL, newH

    return table_rows, (L, H)


def arithmetic_decode(probabilities, code, length, explain=False):
    """
    Decode a float 'code' into 'length' symbols using 'probabilities'.
    Returns:
      - table_rows: A list of rows (lists/tuples) for explanation
      - decoded_message: the resulting string
    """
    cdf, cdf_next, sorted_syms = build_cdf(probabilities)

    L = 0.0
    H = 1.0
    x = code

    table_rows = []
    message = []

    code_str = minimal_decimal_str(x)

    for i in range(1, length + 1):
        # Save old interval for explanation
        oldL = L
        oldH = H

        # Compute interval width
        interval_width = oldH - oldL

        # Find which symbol's subinterval contains x
        found_symbol = None
        for sym in sorted_syms:
            sym_low = oldL + interval_width * cdf[sym]
            sym_high = oldL + interval_width * cdf_next[sym]
            if sym_low <= x < sym_high:
                found_symbol = sym
                # Update the interval for the next iteration
                L, H = sym_low, sym_high
                break

        message.append(found_symbol)

        oldL_str = minimal_decimal_str(oldL)
        oldH_str = minimal_decimal_str(oldH)
        interval_width_str = minimal_decimal_str(interval_width)
        newL_str = minimal_decimal_str(L)
        newH_str = minimal_decimal_str(H)
        table_rows.append([
            i,
            f"{code_str}",
            f"[{oldL_str}, {oldH_str})",
            f"{interval_width_str}",
            f"{found_symbol!r}",
            f"[{newL_str}, {newH_str})"
        ])

    return table_rows, ''.join(message)


def print_encode_table(table_rows, final_interval):
    """
    Print an encoding explanation table, then the final interval and midpoint.
    """
    headers = ["i", "Sym", "CDF Range", "(H_{i-1}-L_{i-1})", "L_i", "H_i"]
    table = tabulate(table_rows, headers=headers, tablefmt="grid")
    print(table)

    L_final, H_final = final_interval
    mid = (L_final + H_final) / 2
    print(f"\nFinal interval: [{minimal_decimal_str(L_final)}, {minimal_decimal_str(H_final)})")
    print(f"Midpoint: {minimal_decimal_str(mid)}")


def print_decode_table(table_rows, decoded):
    """
    Print a decoding explanation table, then the final decoded message.
    """
    headers = ["i", "Code (x)", "Old Interval", "H - L", "Found Symbol", "New Interval [L_i, H_i)"]
    table = tabulate(table_rows, headers=headers, tablefmt="grid")
    print(table)
    print(f"\nDecoded message: {decoded}")


def main():
    parser = argparse.ArgumentParser(
        description="Arithmetic encoding/decoding from the command line."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--encode", action="store_true", help="Encode a string")
    group.add_argument("--decode", action="store_true", help="Decode a float code")

    parser.add_argument("input", help="String to encode (if --encode) or float code (if --decode)")
    parser.add_argument("frequencies", help="Frequencies in the form 'A:0.2,B:0.3,C:0.5,...'")

    parser.add_argument("--explain", action="store_true", help="Show step-by-step table")
    parser.add_argument("--length", type=int, default=None,
                        help="Number of symbols to decode (required if --decode)")

    args = parser.parse_args()

    # Parse the frequencies
    probabilities = parse_frequencies(args.frequencies)

    if not probabilities:
        print('ERROR: Valid probabilities must be provided, adding to 1.0')
        sys.exit(1)

    if args.encode:
        # Input is a string to be encoded
        message = args.input

        if not set(message).issubset(set(probabilities.keys())):
            print('ERROR: Some symbols in the string have not been given a probability')
            sys.exit(1)

        table_rows, (L, H) = arithmetic_encode(probabilities, message, explain=args.explain)

        if args.explain:
            print_encode_table(table_rows, (L, H))
        else:
            # By default, let's just output the midpoint as the code
            midpoint = (L + H) / 2
            print(minimal_decimal_str(midpoint))

    elif args.decode:
        # Input is a float code
        try:
            code_val = float(args.input)
        except ValueError:
            print(f"Error: For decoding, 'input' must be a float. Got '{args.input}'.",
                  file=sys.stderr)
            sys.exit(1)

        # Must have --length specified
        if args.length is None:
            print("Error: --length is required for decoding.", file=sys.stderr)
            sys.exit(1)

        table_rows, decoded = arithmetic_decode(probabilities, code_val, args.length,
                                                explain=args.explain)

        if args.explain:
            print_decode_table(table_rows, decoded)
        else:
            print(decoded)


if __name__ == "__main__":
    main()
