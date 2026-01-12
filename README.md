# Data Compression Tools

This repository provides a set of Python scripts covering different data
compression techniques.

They were developed to assist in the study of _Técnicas de Compresión de
Datos_.

---

## Contents

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Scripts](#scripts)
   - [Huffman](#huffman)
   - [Code Analyzer](#code-analyzer)
   - [LZW](#lzw)
   - [LZ78](#lz78)
   - [Arithmetic Encoding](#arithmetic-encoding)

---

## Overview

Each script demonstrates a different aspect of data compression. Some scripts
can **compress** and **decompress** textual data, others analyze code
properties (prefix, Huffman, unique decodability), and other build a static
Huffman code for a given input string.

Except for `huffman_gui.py`, which displays a window, all of them run fully
from the terminal.

---

## Requirements

- Python 3.6+
- The libraries listed in **requirements.txt**.

To install all dependencies:

```bash
    pip install -r requirements.txt
```

---

## Scripts

### Huffman (CLI)

- **File**: `huffman.py`
- **Description**:
  Builds a static Huffman code from the frequencies of symbols in a given
  string. Can also display the code, the frequency/probability table, average
  code length, and entropy.

**Usage:**
```bash
    python3 huffman.py [--explain] "YOUR_STRING"
```

If `--explain` is provided, it prints detailed information (frequencies,
probabilities, assigned codes, entropy, etc.).

---

### Huffman (GUI)

- **File**: `huffman_gui.py`
- **Description**:
  Interactively builds a static Huffman code from the frequencies of symbols in
  a given string.  It also displays the resulting code, the frequency table,
  average code length, and entropy.

  It can do it step by step, or automatically or all at once, and it can be
  configured to work the classic Huffman way (using a heap, ensuring in each
  step the roots are sorted; or minimizing the number of reorders, which is the
  preferred strategy when doing it by hand to avoid having to rewrite the tree
  too often).

**Usage:**
```bash
    python3 huffman_gui.py
```
---

### Code Analyzer

- **File**: `analyze_code.py`
- **Description**:
  Takes a set of codewords (e.g., `101, 11, 00`) and checks:
  1. Whether the set is a **prefix code**.
  2. Whether it is a **Huffman code** (via Kraft-McMillan sum = 1).
  3. Whether it is **uniquely decodable** (via Sardinas-Patterson if not prefix).

**Usage:**

```bash
    python3 analyze_code.py "101, 11, 00"
```

---

### LZW

- **File**: `LZW.py`
- **Description**:
  Provides **LZW** compression and decompression.

**Compress:**
```bash
    python3 LZW.py --compress "YOUR_STRING"
```

**Decompress:**
```bash
    python3 LZW.py --decompress "3,5,10,27"
```

**Options:**
- `--file FILE` to read input from a file
- `--explain` to display an explanatory table of steps.

---

### LZ78

- **File**: `LZ78.py`
- **Description**:
  Provides **LZ78** compression and decompression.

**Compress:**
```bash
    python3 LZ78.py --compress "YOUR_STRING"
```

**Decompress:**
```bash
    python3 LZ78.py --decompress "(0,H)(0,E)(1,_)..."
```

**Options:**
- `--file FILE` to read input from a file
- `--explain` to display a step-by-step table.

---

### Arithmetic Encoding

- **File**: `arithmetic_encoding.py`
- **Description**:
  Implements **arithmetic encoding** and **decoding** for a given probability distribution.

**Encode:**
```bash
    python3 arithmetic_encoding.py --encode "YOUR_STRING" "A:0.2,B:0.3,C:0.5"
```

**Decode:**
```bash
    python3 arithmetic_encoding.py --decode 0.3725 "A:0.2,B:0.3,C:0.5" --length 5
```

**Options:**
- `--explain` to show interval updates step by step
