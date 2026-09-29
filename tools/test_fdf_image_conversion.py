#!/usr/bin/env python3
"""Verify raw/DMK conversion against the default BetterCP/M disk format."""
from convert_fdf_image import DEFAULT_FDF, DEFAULT_FORMAT, dmk_to_raw, raw_to_dmk
from fdf_format import select_fdf


def expect_failure(action, phrase: str) -> None:
    try:
        action()
    except ValueError as error:
        assert phrase in str(error), error
    else:
        raise AssertionError(f"expected failure containing {phrase!r}")


def main() -> None:
    fmt = select_fdf(DEFAULT_FDF, DEFAULT_FORMAT)
    raw = bytes((track * 19 + slot * 7 + byte) & 0xFF
                for track in range(fmt.raw_tracks)
                for slot in range(fmt.physical_sectors)
                for byte in range(fmt.sector_bytes))
    image = raw_to_dmk(raw, fmt)
    assert len(image) == 16 + fmt.raw_tracks * 0x18EA
    assert image[1] == fmt.cylinders and image[4] == 0
    assert dmk_to_raw(image, fmt) == raw

    first_track = image[16:16 + 0x18EA]
    observed_ids = []
    for index in range(fmt.physical_sectors):
        pointer = int.from_bytes(first_track[index * 2:index * 2 + 2], "little")
        observed_ids.append(first_track[(pointer & 0x3FFF) + 3])
    assert tuple(observed_ids) == fmt.sector_ids

    damaged = bytearray(image)
    first_pointer = int.from_bytes(damaged[16:18], "little") & 0x3FFF
    damaged[16 + first_pointer + 5] ^= 1
    expect_failure(lambda: dmk_to_raw(bytes(damaged), fmt), "bad ID CRC")
    expect_failure(lambda: raw_to_dmk(raw[:-1], fmt), "expected 368640 raw bytes")

    fm = select_fdf(DEFAULT_FDF, "Acorn (80T, SS, SD, 392K)")
    expect_failure(lambda: raw_to_dmk(bytes(fm.image_bytes), fm), "FM conversion is not implemented")

    inverted = select_fdf(DEFAULT_FDF, "Columbia 964 (40T, SS, DD, 190K)")
    inverted_raw = bytes((index * 13) & 0xFF for index in range(inverted.image_bytes))
    assert dmk_to_raw(raw_to_dmk(inverted_raw, inverted), inverted) == inverted_raw
    print("PASS: CCS 332K and inverted raw/DMK round trips, rotational IDs, CRC and scope checks")


if __name__ == "__main__":
    main()
