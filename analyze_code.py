#!/usr/bin/env python3
import argparse
from fractions import Fraction


def parse_codewords(input_string):
    """
    Parse a string like "word1, word2, word3" into a list of codewords.
    Whitespace around each word is stripped.
    """
    # Split on commas
    parts = [p.strip() for p in input_string.split(',')]
    # Filter out any empty parts (if the user typed a trailing comma, etc.)
    return [p for p in parts if p != ""]

def is_prefix_code(codewords):
    """
    Returns True if no codeword is a prefix of another. Otherwise False.
    """
    # A quick way is to sort by length (or lexicographically) and check prefixes.
    sorted_codewords = sorted(codewords)
    n = len(sorted_codewords)

    # We'll do a nested check: for each pair, see if one is prefix of the other
    for i in range(n):
        for j in range(i+1, n):
            w1 = sorted_codewords[i]
            w2 = sorted_codewords[j]
            # If w1 is prefix of w2 or w2 is prefix of w1
            if w2.startswith(w1):
                print(f"Found prefix: '{w1}' is a prefix of '{w2}'")
                return False
            # Because of sorting, w1 <= w2 lexicographically,
            # no need to check w1.startswith(w2) except they might be equal,
            # but presumably no duplicates. If duplicates exist, that also kills prefix property.
    print("No codeword is prefix of another.")
    return True

def kraft_sum(codewords):
    """
    Computes the Kraft sum exactly:
    sum( r^(-len(w)) for w in codewords ), using rational arithmetic.
    """
    r = set(c for word in codewords for c in word)
    radix = len(r)

    if radix == 0:
        return Fraction(0, 1)

    return sum(
        Fraction(1, radix ** len(w))
        for w in codewords
    )

def is_huffman_code(codewords):
    """
    Check if the codewords satisfy Kraft's inequality with equality (= 1)
    using exact fraction checking.
    """
    ksum = kraft_sum(codewords)
    equals_one = (ksum == Fraction(1, 1))
    print(f"Kraft sum = {ksum}; equals 1 => {equals_one}")
    return equals_one


def sardinas_patterson(codewords):
    """
    Apply Sardinas-Patterson algorithm to check unique decodability
    for a non-prefix code.
    Returns True if uniquely decodable, False otherwise.
    """
    # Convert codewords to a set for convenience
    C = set(codewords)

    def left_residual(X, Y):
        """
        L^R(X, Y) = { suffix of y after removing prefix x
                      if y.startswith(x) }
        """
        result = set()
        for x in X:
            for y in Y:
                if len(y) >= len(x) and y.startswith(x):
                    suffix = y[len(x):]
                    # If suffix != "", we include it. The standard algorithm
                    # might keep the empty suffix if x != y; let's keep the standard approach:
                    result.add(suffix)
        return result

    # 1) E1 = L^R(C, C), excluding identical pairs if needed
    E = set()
    for x in C:
        for y in C:
            if x != y and y.startswith(x):
                suffix = y[len(x):]
                E.add(suffix)

    k = 1
    print(f"E1 = {E if E else '{}'}")

    # If empty string in E1 => not UD
    if "" in E:
        print("Empty string in E1 => code is NOT uniquely decodable.")
        return False

    # 2) Iterate
    while True:
        # E_{k+1} = L^R(E_k, C) ∪ L^R(C, E_k)
        E_next = left_residual(E, C) | left_residual(C, E)
        k += 1
        print(f"E{k} = {E_next if E_next else '{}'}")

        if "" in E_next:
            print(f"Empty string in E{k} => code is NOT uniquely decodable.")
            return False

        # If E_{k+1} is a subset of E_k (i.e. stable or no new elements), => UD
        if E_next.issubset(E):
            print("No new elements added => code IS uniquely decodable.")
            return True

        # Otherwise continue
        E = E_next

def main():
    parser = argparse.ArgumentParser(description="Analyze a set of codewords.")
    parser.add_argument("input", help="String of comma-separated codewords, e.g. '101, 11, 00'")
    args = parser.parse_args()

    codewords = parse_codewords(args.input)

    print("Codewords:", codewords, "\n")

    # 1) Check prefix code
    print("=== Checking Prefix Property ===")
    prefix_result = is_prefix_code(codewords)
    print(f"Prefix code? {prefix_result}\n")

    # 2) Check Huffman code (Kraft sum = 1?)
    print("=== Checking Huffman (Kraft) ===")
    if not prefix_result:
        print('Since it is not a prefix code, it cannot be a Huffman code')
        huffman_result = False
    else:
        huffman_result = is_huffman_code(codewords)
    print(f"Huffman code? {huffman_result}\n")

    # 3) Check unique decodability
    #    - If prefix_result is True => automatically UD
    #    - Else run Sardinas-Patterson
    if not prefix_result:
        print("=== Checking Unique Decodability via Sardinas-Patterson ===")
        ud_result = sardinas_patterson(codewords)
    else:
        print("=== Checking Unique Decodability ===")
        ud_result = True
        print("Since it is a prefix code, it is uniquely decodable")
    print(f"Uniquely decodable? {ud_result}\n")

    # Final verdict:
    print("=== Final Verdict ===")
    print(f"Prefix code: {prefix_result}")
    print(f"Huffman code: {huffman_result}")
    print(f"Uniquely decodable: {ud_result}")

if __name__ == "__main__":
    main()
