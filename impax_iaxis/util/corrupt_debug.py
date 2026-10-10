import sys

axis_apids = [
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

ansi = {
    "black": "\x1b[30m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "purple": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
    "reset": "\x1b[0m",
}


def printc(*args, color=None, end="\n", sep=" "):
    """Like print(), but with color."""
    if color is not None:
        print(ansi[color.lower()], *args, ansi["reset"], end=end, sep=sep)
    else:
        print(*args, end=end, sep=sep)


def apid_at(k: int, buff: bytes):
    """Get the APID of this CCSDS packet, assuming k is at the beginning of the packet."""
    return 0x7FF & int.from_bytes(buff[k : k + 2], byteorder="big", signed=False)


def length_at(k: int, buff: bytes):
    """Get the length field of this CCSDS packet, assuming k is at the beginning of the packet."""
    return 0xFFFF & int.from_bytes(buff[k + 4 : k + 6], byteorder="big", signed=False)


def time_at(k: int, buff: bytes):
    ct = 0xFFFFFFFF & int.from_bytes(
        buff[k + 6 : k + 10], byteorder="big", signed=False
    )
    ft = 0xFFFF & int.from_bytes(buff[k + 10 : k + 12], byteorder="big", signed=False)
    return ct + ft / 1000


def recover_print(file: str, valid_apids=axis_apids):
    """Seek through a file full of CCSDS and print loudly when find an APID not in the valid_apids list."""
    with open(file, "rb") as f:
        buff = f.read()

    counts = {}
    goods = 0  # count packets with good APID
    bads = 0  # count packets with bad APID
    badk = 0  # offset of last bad APID
    unhappy = False  # keep track of mood (wrt APID)
    prior_apid = 0x00  # last good APID we saw
    prior_unhappy_time = 0.0
    prior_time = 0.0
    k = 0

    while k < len(buff):
        maybe_apid = apid_at(k, buff)
        if maybe_apid in valid_apids:
            # ok, this really does look like an AXIS APID.
            prior_apid = maybe_apid
            prior_time = time_at(k, buff)
            if unhappy:
                # if we had APID issues before, looks like we've recovered
                printc(
                    f"Recovered {k - badk} bytes later with APID 0x{prior_apid:x}.",
                    color="green",
                )
                unhappy = False
            # advance to next packet. 6 = CCSDS header length. 1 = just past the end of the packet.
            # padlen259 = -2 if prior_apid == 0x259 else 0
            k += length_at(k, buff) + 6 + 1  # + padlen259
            goods += 1
            counts[prior_apid] = counts.get(prior_apid, 0) + 1
            # actually probably an off-by-one error here in total goods count...

        elif maybe_apid not in valid_apids and not unhappy:
            # become unhappy. and don't do it quietly.
            printc(
                f"\nFound bad APID at offset 0x{k:x}, last APID 0x{prior_apid:x}, {(prior_time - prior_unhappy_time):.2f} s ago. Context:",
                color="red",
            )
            print("...", end="")
            printc(buff[max(0, k - 20) : k].hex(), end="")
            printc(buff[k : k + 2].hex(), color="red", end="")
            printc(buff[k + 2 : min(len(buff) - 1, k + 22)].hex(), end="")
            print("...")

            unhappy = True
            prior_unhappy_time = prior_time
            bads += 1
            badk = k

        else:
            # if we're unhappy, seek through the file until we find an APID again.
            k += 1

    print(f"\nFound a total of {bads}/{goods} bad/good APID packets.")
    print("Distribution of APIDs:")
    [print(f"\t0x{id:x}: {count}") for id, count in counts.items()]


if __name__ == "__main__":
    if sys.argv[1] == "help" or sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print("run like this:\n\t> python corrupt_debug.py path/to/raw/telemetry/file")
        sys.exit(0)
    src = sys.argv[1]
    recover_print(src)
