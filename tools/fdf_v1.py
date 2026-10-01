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


class FDBError(ValueError):
    """A structural or semantic error in a compiled FDB catalogue."""


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


@dataclass(frozen=True)
class FDBDescriptor:
    ident: str
    description: str
    supported: bool
    unsupported_required: tuple[int, ...]
    format: Format | None


@dataclass(frozen=True)
class FDB:
    minor: int
    crc: int
    descriptors: tuple[FDBDescriptor, ...]


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


def _padded_text(raw: bytes, field: str, pattern: str | None = None) -> str:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        raise FDBError(f"{field}: non-ASCII byte") from None
    value = text.rstrip(" ")
    if not value or text[len(value):] != " " * (len(text) - len(value)):
        raise FDBError(f"{field}: invalid space padding")
    if pattern is not None and not re.fullmatch(pattern, value):
        raise FDBError(f"{field}: invalid value {value!r}")
    if any(not 32 <= ord(char) <= 126 for char in value):
        raise FDBError(f"{field}: non-printable character")
    return value


def read_fdb(data: bytes) -> FDB:
    """Validate and decode one complete FDB v1 file."""
    if not data or len(data) % 128 or len(data) > 0xFF80:
        raise FDBError("file length must be 1..511 complete CP/M records")
    if len(data) < 128:
        raise FDBError("file is shorter than the first record")
    magic, major, minor, header_size, stride, count, first, pool, stored_crc = \
        struct.unpack_from("<4sBBBBHHHH", data)
    if magic != b"BFDB" or major != 1:
        raise FDBError("unknown FDB signature or major version")
    if header_size < 16 or stride < 64:
        raise FDBError("header size or descriptor stride is too small")
    if first != 128 or pool != first + count * stride or pool > len(data):
        raise FDBError("descriptor table offsets are inconsistent")
    if header_size > first or any(data[header_size:first]):
        raise FDBError("reserved header bytes are nonzero")
    check = bytearray(data)
    check[14:16] = b"\0\0"
    if crc16(check) != stored_crc:
        raise FDBError("CRC-16 does not match the complete file")

    owned = bytearray(len(data))
    descriptors = []
    identifiers = set()
    highest = pool

    def own(start: int, end: int, label: str) -> None:
        nonlocal highest
        if start < pool or end <= start or end > len(data):
            raise FDBError(f"{label}: pool object is out of bounds")
        if any(owned[start:end]):
            raise FDBError(f"{label}: pool objects overlap")
        owned[start:end] = b"\x01" * (end - start)
        highest = max(highest, end)

    for index in range(count):
        start = first + index * stride
        record = data[start:start + 64]
        ident = _padded_text(record[0:8], f"descriptor {index} ID", r"[A-Z0-9]{1,8}")
        if ident in identifiers:
            raise FDBError(f"duplicate descriptor ID {ident}")
        identifiers.add(ident)
        description = _padded_text(record[8:40], f"{ident} description")
        spt, bsh, blm, exm, dsm, drm, al0, al1, cks, off = \
            struct.unpack_from("<HBBBHHBBHH", record, 40)
        psectors, size_code, cylinders, flags, id_count = record[55:60]
        id_offset, extension_offset = struct.unpack_from("<HH", record, 60)
        if id_count != psectors or not psectors:
            raise FDBError(f"{ident}: duplicated sector count is invalid")
        if size_code not in range(4) or not cylinders:
            raise FDBError(f"{ident}: sector size code or cylinder count is invalid")
        own(id_offset, id_offset + id_count, f"{ident} sector IDs")
        sector_ids = tuple(data[id_offset:id_offset + id_count])
        if len(set(sector_ids)) != len(sector_ids):
            raise FDBError(f"{ident}: sector IDs are not distinct")
        if bool(flags & 0x80) != bool(extension_offset):
            raise FDBError(f"{ident}: extension flag and offset disagree")

        extensions: dict[int, bytes] = {}
        unsupported = []
        if extension_offset:
            cursor = extension_offset
            while True:
                if cursor + 2 > len(data):
                    raise FDBError(f"{ident}: unterminated extension list")
                kind_byte, length = data[cursor:cursor + 2]
                cursor += 2
                if kind_byte == 0:
                    if length:
                        raise FDBError(f"{ident}: type zero has nonzero length")
                    extension_end = cursor
                    break
                if kind_byte == 0x80:
                    raise FDBError(f"{ident}: required extension kind zero is invalid")
                end = cursor + length
                if end > len(data):
                    raise FDBError(f"{ident}: extension payload is out of bounds")
                kind = kind_byte & 0x7F
                if kind in extensions:
                    raise FDBError(f"{ident}: repeated extension kind {kind}")
                payload = data[cursor:end]
                extensions[kind] = payload
                if kind in (1, 2) and not kind_byte & 0x80:
                    raise FDBError(f"{ident}: semantic extension {kind} is not required")
                if kind not in (1, 2) and kind_byte & 0x80:
                    unsupported.append(kind)
                cursor = end
            own(extension_offset, extension_end, f"{ident} extensions")

        sector_sizes = None
        if 1 in extensions:
            payload = extensions[1]
            if len(payload) != psectors or any(code not in range(4) for code in payload):
                raise FDBError(f"{ident}: mixed-sector extension is malformed")
            if max(payload) != size_code:
                raise FDBError(f"{ident}: mixed-sector maximum disagrees with SECSIZE")
            sector_sizes = tuple(128 << code for code in payload)
        logical_track = "SURFACE"
        if 2 in extensions:
            if extensions[2] != b"\x01":
                raise FDBError(f"{ident}: logical-track extension is malformed")
            logical_track = "CYLINDER"

        item = None
        if not unsupported:
            fields = {
                "ID": (ident, 0), "DESCRIPTION": (description, 0),
                "SPT": (str(spt), 0), "BSH": (str(bsh), 0),
                "BLM": (str(blm), 0), "EXM": (str(exm), 0),
                "DSM": (str(dsm), 0), "DRM": (str(drm), 0),
                "AL0": (str(al0), 0), "AL1": (str(al1), 0),
                "CKS": (str(cks), 0), "OFF": (str(off), 0),
                "PSECTORS": (str(psectors), 0),
                "SECSIZE": (str(128 << size_code), 0),
                "CYLINDERS": (str(cylinders), 0),
                "SIDES": ("2" if flags & 1 else "1", 0),
                "ENCODING": ("MFM" if flags & 2 else "FM", 0),
                "INVERT": ("YES" if flags & 4 else "NO", 0),
                "SECTOR_IDS": (",".join(map(str, sector_ids)), 0),
                "LOGICAL_TRACK": (logical_track, 0),
                "SIDE_ORDER": ("SIDE_MAJOR" if flags & 8 else "ALTERNATING", 0),
                "SIDE1_DIRECTION": ("REVERSE" if flags & 16 else "FORWARD", 0),
                "TRACK_ID_MODE": ("CONTINUOUS" if flags & 32 else "PER_CYLINDER", 0),
                "SECTOR_ID_MODE": ("CONTINUOUS" if flags & 64 else "RESTART", 0),
            }
            if sector_sizes is not None:
                fields["SECTOR_SIZES"] = (",".join(map(str, sector_sizes)), 0)
            try:
                item = _make(fields)
            except FDFError as error:
                raise FDBError(f"{ident}: {error}") from None
        descriptors.append(FDBDescriptor(
            ident, description, not unsupported, tuple(sorted(unsupported)), item))

    expected_size = (highest + 127) & ~127
    if len(data) != expected_size:
        raise FDBError("file has arbitrary extra record padding")
    for offset in range(pool, len(data)):
        if not owned[offset] and data[offset]:
            raise FDBError(f"nonzero unowned pool byte at {offset:04X}h")
    return FDB(minor, stored_crc, tuple(descriptors))


def compile_file(path: Path) -> bytes:
    raw = path.read_bytes()
    raw = raw.split(b"\x1a", 1)[0]
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise FDFError(f"{path}: source is not ASCII") from error
    return serialize(parse(text, str(path)))


def read_fdb_file(path: Path) -> FDB:
    try:
        return read_fdb(path.read_bytes())
    except OSError as error:
        raise FDBError(f"{path}: {error}") from error
