"""Parse and normalize Montezuma-style DISK.FDF format definitions."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FDFFormat:
    name: str
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
    physical_sectors: int
    size_code: int
    cylinders: int
    flags: int
    sector_ids: tuple[int, ...]

    @property
    def sector_bytes(self) -> int:
        return 128 << self.size_code

    @property
    def sides(self) -> int:
        return 2 if self.flags & 0x60 else 1

    @property
    def raw_tracks(self) -> int:
        return self.cylinders * self.sides

    @property
    def raw_track_bytes(self) -> int:
        return self.physical_sectors * self.sector_bytes

    @property
    def image_bytes(self) -> int:
        return self.raw_tracks * self.raw_track_bytes

    @property
    def block_bytes(self) -> int:
        return 128 << self.bsh

    @property
    def reserved_records(self) -> int:
        return self.spt * self.off

    @property
    def directory_blocks(self) -> int:
        return bin(self.al0 << 8 | self.al1).count("1")

    def binding(self, physical_drive: int) -> bytes:
        if not 0 <= physical_drive < 16:
            raise ValueError("physical drive must be 0..15")
        result = bytearray(64)
        result[0] = physical_drive
        result[1:3] = self.spt.to_bytes(2, "little")
        result[3:6] = bytes((self.bsh, self.blm, self.exm))
        result[6:8] = self.dsm.to_bytes(2, "little")
        result[8:10] = self.drm.to_bytes(2, "little")
        result[10:12] = bytes((self.al0, self.al1))
        result[12:14] = self.cks.to_bytes(2, "little")
        result[14:16] = self.off.to_bytes(2, "little")
        result[16:20] = bytes((self.cylinders, self.physical_sectors,
                               self.size_code, self.flags))
        result[20:20 + len(self.sector_ids)] = bytes(self.sector_ids)
        return bytes(result)

    def raw_record_map(self) -> tuple[int, ...]:
        """Map each 128-byte logical record in a track to a raw record slot."""
        records_per_sector = 1 << self.size_code
        if self.spt != self.physical_sectors * records_per_sector:
            raise ValueError(f"{self.name}: mixed/cylinder SPT needs an explicit size map")
        ordered = sorted(self.sector_ids)
        if len(ordered) != self.physical_sectors or len(set(ordered)) != len(ordered):
            raise ValueError(f"{self.name}: invalid or duplicate sector IDs")
        slots = {sector_id: index for index, sector_id in enumerate(ordered)}
        mapping = []
        for sector_id in self.sector_ids:
            base = slots[sector_id] * records_per_sector
            mapping.extend(base + quarter for quarter in range(records_per_sector))
        return tuple(mapping)


def parse_fdf(path: Path) -> tuple[FDFFormat, ...]:
    lines = path.read_text(encoding="ascii").splitlines()
    formats: list[FDFFormat] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        if not line.startswith("*"):
            continue
        name = line[1:].strip()
        if index + 1 >= len(lines):
            raise ValueError(f"{path}: incomplete definition for {name}")
        fields = tuple(int(value.strip()) for value in lines[index].split(","))
        index += 1
        if len(fields) != 14:
            raise ValueError(f"{path}: {name} has {len(fields)} fields, expected 14")
        sector_ids = tuple(int(value.strip()) for value in lines[index].split(","))
        index += 1
        if len(sector_ids) != fields[10]:
            raise ValueError(f"{path}: {name} sector table length mismatch")
        formats.append(FDFFormat(name, *fields, sector_ids))
    return tuple(formats)


def select_fdf(path: Path, name: str) -> FDFFormat:
    wanted = name.casefold()
    matches = [item for item in parse_fdf(path) if item.name.casefold() == wanted]
    if len(matches) != 1:
        raise ValueError(f"DISK.FDF format not found: {name}")
    return matches[0]
