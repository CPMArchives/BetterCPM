"""BetterCP/M FDF v1 parser, validator, and deterministic FDB serializer."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import struct


SIZE_CODES = {128: 0, 256: 1, 512: 2, 1024: 3}
MANDATORY = {
    "ID", "SPT", "BSH", "DSM", "DRM", "AL0", "AL1", "CKS", "OFF",
    "PSECTORS", "SECSIZE", "CYLINDERS", "SIDES", "ENCODING", "SECTOR_IDS",
}
OPTIONAL = {
    "DESCRIPTION", "BLM", "EXM", "INVERT", "SECTOR_SIZES",
    "LOGICAL_TRACK", "SIDE_ORDER", "SIDE1_DIRECTION", "TRACK_ID_MODE",
    "SECTOR_ID_MODE",
}


class FDFError(ValueError):
    """A source or semantic error in an FDF v1 catalogue."""


@dataclass(frozen=True)
class Format:
    ident: str
    description: str
    spt: int
    bsh: int
    blm: int
    exm: int
    dsm: int
    drm: int
    al0: int
    al1: int
    cks: int
    off: int
    psectors: int
    secsize: int
    cylinders: int
    sides: int
    encoding: str
    invert: bool
    sector_ids: tuple[int, ...]
    sector_sizes: tuple[int, ...] | None
    logical_track: str
    side_order: str
    side1_direction: str
    track_id_mode: str
    sector_id_mode: str

    @property
    def flags(self) -> int:
        return ((1 if self.sides == 2 else 0) |
                (2 if self.encoding == "MFM" else 0) |
                (4 if self.invert else 0) |
                (8 if self.side_order == "SIDE_MAJOR" else 0) |
                (16 if self.side1_direction == "REVERSE" else 0) |
                (32 if self.track_id_mode == "CONTINUOUS" else 0) |
                (64 if self.sector_id_mode == "CONTINUOUS" else 0) |
                (128 if self.extensions else 0))

    @property
    def extensions(self) -> tuple[tuple[int, bytes], ...]:
        result = []
        if self.sector_sizes is not None and len(set(self.sector_sizes)) > 1:
            result.append((0x81, bytes(SIZE_CODES[size] for size in self.sector_sizes)))
        if self.logical_track == "CYLINDER":
            result.append((0x82, b"\x01"))
        return tuple(result)


def _uncomment(raw: str) -> str:
    quoted = False
    for index, char in enumerate(raw):
        if char == '"':
            quoted = not quoted
        elif char == "#" and not quoted:
            return raw[:index]
    if quoted:
        raise FDFError("unterminated quoted string")
    return raw


def _number(value: str, field: str) -> int:
    if not re.fullmatch(r"(?:0[xX][0-9A-Fa-f]+|[0-9]+)", value):
        raise FDFError(f"{field}: expected unsigned decimal or hexadecimal number")
    return int(value, 0)


def _list(value: str, field: str) -> tuple[int, ...]:
    parts = [item.strip() for item in value.split(",")]
    if not parts or any(not item for item in parts):
        raise FDFError(f"{field}: malformed or empty list element")
    return tuple(_number(item, field) for item in parts)


def _enum(fields: dict[str, tuple[str, int]], name: str, default: str,
          allowed: tuple[str, ...]) -> str:
    value = fields.get(name, (default, 0))[0].upper()
    if value not in allowed:
        raise FDFError(f"{name}: expected {' or '.join(allowed)}")
    return value


def _bounded(fields: dict[str, tuple[str, int]], name: str, maximum: int) -> int:
    value = _number(fields[name][0], name)
    if value > maximum:
        raise FDFError(f"{name}: {value} exceeds {maximum}")
    return value


def _make(fields: dict[str, tuple[str, int]]) -> Format:
    missing = sorted(MANDATORY - fields.keys())
    if missing:
        raise FDFError("missing required field(s): " + ", ".join(missing))
    unknown = sorted(fields.keys() - MANDATORY - OPTIONAL)
    if unknown:
        raise FDFError("unknown field(s): " + ", ".join(unknown))

    ident = fields["ID"][0].upper()
    if not re.fullmatch(r"[A-Z0-9]{1,8}", ident):
        raise FDFError("ID: expected 1-8 ASCII letters or digits")
    description = fields.get("DESCRIPTION", (ident, 0))[0]
    if not 1 <= len(description) <= 32 or any(not 32 <= ord(c) <= 126 for c in description):
        raise FDFError("DESCRIPTION: expected 1-32 printable ASCII characters")

    spt = _bounded(fields, "SPT", 0xFFFF)
    bsh = _bounded(fields, "BSH", 7)
    if bsh < 3:
        raise FDFError("BSH: expected 3..7")
    blm = (1 << bsh) - 1
    if "BLM" in fields and _bounded(fields, "BLM", 0xFF) != blm:
        raise FDFError(f"BLM: expected {blm} for BSH {bsh}")
    dsm = _bounded(fields, "DSM", 0xFFFF)
    drm = _bounded(fields, "DRM", 0xFFFF)
    al0 = _bounded(fields, "AL0", 0xFF)
    al1 = _bounded(fields, "AL1", 0xFF)
    cks = _bounded(fields, "CKS", 0xFFFF)
    off = _bounded(fields, "OFF", 0xFFFF)
    if dsm >= 256 and bsh == 3:
        raise FDFError("DSM >= 256 is not representable with BSH 3")
    exm_max = (1 << (bsh - (4 if dsm >= 256 else 3))) - 1
    exm = _number(fields.get("EXM", (str(exm_max), 0))[0], "EXM")
    if exm > exm_max or exm & (exm + 1):
        raise FDFError(f"EXM: expected a contiguous mask no greater than {exm_max}")

    psectors = _bounded(fields, "PSECTORS", 255)
    cylinders = _bounded(fields, "CYLINDERS", 255)
    if not psectors or not cylinders or not spt:
        raise FDFError("SPT, PSECTORS, and CYLINDERS must be nonzero")
    secsize = _number(fields["SECSIZE"][0], "SECSIZE")
    if secsize not in SIZE_CODES:
        raise FDFError("SECSIZE: expected 128, 256, 512, or 1024")
    sides = _number(fields["SIDES"][0], "SIDES")
    if sides not in (1, 2):
        raise FDFError("SIDES: expected 1 or 2")
    encoding = _enum(fields, "ENCODING", "", ("FM", "MFM"))
    invert = _enum(fields, "INVERT", "NO", ("NO", "YES")) == "YES"
    sector_ids = _list(fields["SECTOR_IDS"][0], "SECTOR_IDS")
    if len(sector_ids) != psectors or len(set(sector_ids)) != psectors:
        raise FDFError("SECTOR_IDS: count must equal PSECTORS and IDs must be distinct")
    if any(value > 255 for value in sector_ids):
        raise FDFError("SECTOR_IDS: IDs must fit one byte")
    sector_sizes = (_list(fields["SECTOR_SIZES"][0], "SECTOR_SIZES")
                    if "SECTOR_SIZES" in fields else None)
    if sector_sizes is not None:
        if len(sector_sizes) != psectors or any(size not in SIZE_CODES for size in sector_sizes):
            raise FDFError("SECTOR_SIZES: count and allowed sizes are invalid")
        if max(sector_sizes) != secsize:
            raise FDFError("SECTOR_SIZES: maximum must equal SECSIZE")
    sizes = sector_sizes or (secsize,) * psectors
    records = sum(sizes) // 128

    logical_track = _enum(fields, "LOGICAL_TRACK", "SURFACE", ("SURFACE", "CYLINDER"))
    side_order = _enum(fields, "SIDE_ORDER", "ALTERNATING", ("ALTERNATING", "SIDE_MAJOR"))
    side1_direction = _enum(fields, "SIDE1_DIRECTION", "FORWARD", ("FORWARD", "REVERSE"))
    track_id_mode = _enum(fields, "TRACK_ID_MODE", "PER_CYLINDER", ("PER_CYLINDER", "CONTINUOUS"))
    sector_id_mode = _enum(fields, "SECTOR_ID_MODE", "RESTART", ("RESTART", "CONTINUOUS"))
    if logical_track == "SURFACE":
        expected_spt = records
    else:
        if sides != 2 or (side_order, side1_direction, track_id_mode, sector_id_mode) != \
                ("ALTERNATING", "FORWARD", "PER_CYLINDER", "RESTART"):
            raise FDFError("CYLINDER requires two sides and default topology")
        expected_spt = records * 2
    if spt != expected_spt:
        raise FDFError(f"SPT: expected {expected_spt} from recorded sectors")
    if side1_direction == "REVERSE" and side_order != "SIDE_MAJOR":
        raise FDFError("SIDE1_DIRECTION REVERSE requires SIDE_MAJOR")
    if sides == 1 and (side_order != "ALTERNATING" or side1_direction != "FORWARD" or
                       track_id_mode != "PER_CYLINDER" or sector_id_mode != "RESTART"):
        raise FDFError("single-sided definitions require default topology")
    if track_id_mode == "CONTINUOUS" and cylinders * 2 - 1 > 255:
        raise FDFError("TRACK_ID_MODE CONTINUOUS overflows byte-valued IDs")
    if sector_id_mode == "CONTINUOUS" and max(sector_ids) + psectors > 255:
        raise FDFError("SECTOR_ID_MODE CONTINUOUS overflows byte-valued IDs")

    block_records = 1 << bsh
    directory_blocks = ((drm + 1) * 32 + block_records * 128 - 1) // (block_records * 128)
    bitmap = al0 << 8 | al1
    if directory_blocks > 16:
        raise FDFError("directory requires more than 16 allocation-map blocks")
    required = ((1 << directory_blocks) - 1) << (16 - directory_blocks) if directory_blocks else 0
    if bitmap & required != required:
        raise FDFError("AL0/AL1 do not reserve every directory block")
    logical_tracks = cylinders if logical_track == "CYLINDER" else cylinders * sides
    total_records = logical_tracks * spt
    allocated_records = (dsm + 1) * block_records
    if allocated_records > 0x10000:
        raise FDFError("allocation exceeds the CP/M 2.2 record-address range")
    if off * spt + allocated_records > total_records:
        raise FDFError("reserved and allocated records exceed recorded capacity")

    return Format(ident, description, spt, bsh, blm, exm, dsm, drm, al0, al1,
                  cks, off, psectors, secsize, cylinders, sides, encoding, invert,
                  sector_ids, sector_sizes, logical_track, side_order,
                  side1_direction, track_id_mode, sector_id_mode)


def parse(text: str, source: str = "<input>") -> tuple[Format, ...]:
    meaningful = []
    for number, raw in enumerate(text.splitlines(), 1):
        if "\x1a" in raw:
            raw = raw.split("\x1a", 1)[0]
            stop = True
        else:
            stop = False
        try:
            line = _uncomment(raw).strip()
        except FDFError as error:
            raise FDFError(f"{source}:{number}: {error}") from None
        if line:
            meaningful.append((number, line))
        if stop:
            break
    if not meaningful or meaningful[0][1].upper().split() != ["FDF_VERSION", "1"]:
        raise FDFError(f"{source}: first meaningful statement must be FDF_VERSION 1")
    formats = []
    fields: dict[str, tuple[str, int]] | None = None
    ids = set()
    for number, line in meaningful[1:]:
        parts = line.split(None, 1)
        keyword = parts[0].upper()
        value = parts[1].strip() if len(parts) == 2 else ""
        if keyword == "FORMAT":
            if value or fields is not None:
                raise FDFError(f"{source}:{number}: invalid or nested FORMAT")
            fields = {}
            continue
        if keyword == "END":
            if value or fields is None:
                raise FDFError(f"{source}:{number}: END without FORMAT")
            try:
                item = _make(fields)
            except FDFError as error:
                ident = fields.get("ID", ("<unknown>", 0))[0]
                raise FDFError(f"{source}:{number}: {ident}: {error}") from None
            if item.ident in ids:
                raise FDFError(f"{source}:{number}: duplicate ID {item.ident}")
            ids.add(item.ident)
            formats.append(item)
            fields = None
            continue
        if fields is None:
            raise FDFError(f"{source}:{number}: statement outside FORMAT")
        if not value:
            raise FDFError(f"{source}:{number}: {keyword} requires a value")
        if keyword in fields:
            raise FDFError(f"{source}:{number}: duplicate field {keyword}")
        if keyword == "DESCRIPTION":
            if len(value) < 2 or value[0] != '"' or value[-1] != '"' or '"' in value[1:-1]:
                raise FDFError(f"{source}:{number}: DESCRIPTION requires one quoted string")
            value = value[1:-1]
        fields[keyword] = (value, number)
    if fields is not None:
        raise FDFError(f"{source}: unterminated FORMAT")
    return tuple(formats)


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def serialize(formats: tuple[Format, ...]) -> bytes:
    if len(formats) > (0xFF80 - 128) // 64:
        raise FDFError("descriptor table exceeds the 16-bit FDB envelope")
    descriptor_offset = 128
    pool_offset = descriptor_offset + len(formats) * 64
    pool = bytearray()
    descriptors = bytearray()
    for item in formats:
        id_offset = pool_offset + len(pool)
        pool.extend(item.sector_ids)
        extension_offset = 0
        if item.extensions:
            extension_offset = pool_offset + len(pool)
            for kind, payload in item.extensions:
                pool.extend((kind, len(payload)))
                pool.extend(payload)
            pool.extend((0, 0))
        dpb = struct.pack("<HBBBHHBBHH", item.spt, item.bsh, item.blm, item.exm,
                          item.dsm, item.drm, item.al0, item.al1, item.cks, item.off)
        descriptors.extend(item.ident.encode("ascii").ljust(8, b" "))
        descriptors.extend(item.description.encode("ascii").ljust(32, b" "))
        descriptors.extend(dpb)
        descriptors.extend((item.psectors, SIZE_CODES[item.secsize],
                            item.cylinders, item.flags, item.psectors))
        descriptors.extend(struct.pack("<HH", id_offset, extension_offset))
    size = (pool_offset + len(pool) + 127) & ~127
    if size > 0xFF80:
        raise FDFError("serialized database exceeds 65,408 bytes")
    result = bytearray(size)
    result[:16] = struct.pack("<4sBBBBHHHH", b"BFDB", 1, 0, 16, 64,
                              len(formats), descriptor_offset, pool_offset, 0)
    result[descriptor_offset:pool_offset] = descriptors
    result[pool_offset:pool_offset + len(pool)] = pool
    result[14:16] = crc16(result).to_bytes(2, "little")
    return bytes(result)


def compile_file(path: Path) -> bytes:
    raw = path.read_bytes()
    raw = raw.split(b"\x1a", 1)[0]
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise FDFError(f"{path}: source is not ASCII") from error
    return serialize(parse(text, str(path)))
