"""
This module provides a generic file reader.
"""

__all__ = ["process_file", "read_file"]
import csv
import json
import os
import pprint
import sys
import warnings

import ccsdspy

from ..io.cdf import cdf_from_apid
from ..util.exceptions import warn_user

axis_valid_apids = [
    0x220,
    0x221,
    0x222,
    0x223,
    0x224,
    0x225,
    0x226,
    0x250,
    0x251,
    0x252,
    0x253,
    0x254,
    0x255,
    0x256,
    0x257,
    0x258,
    0x259,
    0x25A,
    0x25B,
    0x25C,
    0x25D,
]


def split_csv_defs_by_apid(packet_defs: str):
    with open(packet_defs, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quotechar='"')

        keep_keys = ["name", "bit_length", "data_type", "byte_order", "description"]

        by_apid = {}
        for row in reader:
            if row["apid"] == "":
                continue
            this_apid = int(row["apid"], base=16)
            this_field = {k: row[k] for k in row}
            if this_apid not in by_apid:
                by_apid[this_apid] = [this_field]
            else:
                by_apid[this_apid].append(this_field)
    return by_apid


def write_by_apid(by_apid: dict):
    fieldnames = [
        "name",
        "bit_length",
        "data_type",
        "byte_order",
        "unit",
        "source system",
        "class",
        "packet name",
        "description",
        "reference",
    ]

    flookup = {}
    for apid, rows in by_apid.items():
        fname = os.path.join(
            os.path.dirname(__file__), "..", "data", "axis-ccsds_" + hex(apid) + ".csv"
        )
        with open(fname, "w", newline="") as f:
            wr = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                extrasaction="ignore",
                delimiter=",",
                quotechar='"',
            )
            wr.writeheader()
            for row in rows:
                wr.writerow(row)
            print(f"wrote apid {hex(apid)} to {fname}")
            flookup[apid] = fname

    return flookup


def read_file(data_filename):
    """
    Read a file.

    Parameters
    ----------
    data_filename: str
        A file to read.

    Returns
    -------
    data: str

    Examples
    --------
    """

    return


def process_file(fname: str):
    flookup = write_by_apid(
        split_csv_defs_by_apid(
            os.path.join(os.path.dirname(__file__), "..", "data", "axis-ccsds.csv")
        )
    )

    packets = {}
    for f in flookup:
        print(f"building template for apid {hex(f)}")
        packets[f] = ccsdspy.VariableLength.from_file(flookup[f])

    d = ccsdspy.split_by_apid(fname, valid_apids=axis_valid_apids)

    p = {}
    for apid, stream in d.items():
        if apid not in axis_valid_apids:
            warn_user(
                f"apID 0x{apid:x} found in stream but not in list of valid apIDs."
            )
            continue
        if apid not in packets:
            warn_user(f"No packet parser defined for apID 0x{apid:x}.")
            continue
        p[apid] = packets[apid].load(stream, include_primary_header=True)

    return p


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    packet = process_file(sys.argv[1])

    actually_make_cdfs = [0x220, 0x252]

    for p in packet:
        if p in actually_make_cdfs:
            print(f"{p}: {packet[p].keys()}")
            cdf_from_apid(
                p,
                packet[p],
                sys.argv[1],
                os.path.join(os.path.dirname(__file__), "..", "data", "log"),
            )
            print(len(packet[p]["CCSDS_SEQUENCE_COUNT"]))

    print(packet.keys())
