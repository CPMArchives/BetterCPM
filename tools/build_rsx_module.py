#!/usr/bin/env python3
"""Build BetterCP/M BRSX version-1 or version-2 module carriers."""
from __future__ import annotations

import struct

MAGIC = b"BRSX"
HEADER_SIZE = 512
RELOCATION_OFFSET = 48
NO_ENTRY = 0xFFFF
METADATA_MAGIC = b"BMET"
METADATA_HEADER_SIZE = 12
RECORD_NUMERIC_SERVICES = 1
RECORD_CALLABLE_SERVICE = 2
RECORD_RUNTIME_POINTERS = 3
RECONSTRUCTION_CLASSES = {
    "STATELESS": 0,
    "STATEFUL": 1,
    "STATE_PRESERVING": 2,
    "COLD_ONLY": 3,
}


def _record(record_type: int, payload: bytes) -> bytes:
    if not payload or len(payload) > 255:
        raise SystemExit("invalid BRSX metadata record length")
    return bytes((record_type, len(payload))) + payload


def _v2_metadata(services: list[int], callable_services: list[tuple[bytes, int,
                                                                    int, int, int]],
                 runtime_pointers: list[int]) -> bytes:
    records: list[bytes] = []
    if services:
        records.append(_record(RECORD_NUMERIC_SERVICES, bytes(services)))
    for service_id, major, minor, entry, capabilities in callable_services:
        if (len(service_id) != 4 or any(not 0x20 <= byte <= 0x5A
                                        for byte in service_id)
                or not 0 <= major <= 255 or not 0 <= minor <= 255
                or not 0 <= entry <= 0xFFFF
                or not 0 <= capabilities <= 0xFFFF):
            raise SystemExit("invalid callable RSX service advertisement")
        records.append(_record(RECORD_CALLABLE_SERVICE,
                               struct.pack("<4sBBHH", service_id, major, minor,
                                           entry, capabilities)))
    if runtime_pointers:
        records.append(_record(RECORD_RUNTIME_POINTERS,
                               struct.pack(f"<{len(runtime_pointers)}H",
                                           *runtime_pointers)))
    body = b"".join(records)
    return struct.pack("<4sBBBBHH", METADATA_MAGIC, 1, 0,
                       METADATA_HEADER_SIZE, len(records),
                       METADATA_HEADER_SIZE + len(body), 0) + body


def make_module(*, name: str, version: tuple[int, int], services: list[int],
                linked_base: int, code: bytes, relocations: list[int],
                entry_offset: int = 4, init_offset: int = NO_ENTRY,
                shutdown_offset: int = NO_ENTRY, allocation: int | None = None,
                flags: int = 0, format_version: int = 1,
                reconstruction_class: str = "STATELESS",
                callable_services: list[tuple[bytes, int, int, int, int]] | None = None,
                runtime_pointers: list[int] | None = None) -> bytes:
    stem = name.upper().encode("ascii")
    if not 1 <= len(stem) <= 8 or any(not 0 <= service <= 255 for service in services):
        raise SystemExit("invalid RSX name or service number")
    callable_services = [] if callable_services is None else callable_services
    runtime_pointers = [] if runtime_pointers is None else runtime_pointers
    if format_version not in (1, 2):
        raise SystemExit("unsupported BRSX format version")
    if format_version == 1 and (callable_services or runtime_pointers
                                or reconstruction_class != "STATELESS"):
        raise SystemExit("BRSX v1 cannot carry reconstruction metadata")
    if reconstruction_class not in RECONSTRUCTION_CLASSES:
        raise SystemExit("unknown RSX reconstruction class")
    if format_version == 2 and flags & ~3:
        raise SystemExit("BRSX v2 reserved flag bits must be zero")
    if len(callable_services) > 2:
        raise SystemExit("BRSX v2 supports at most two callable services")
    if runtime_pointers != sorted(set(runtime_pointers)):
        raise SystemExit("runtime pointer slots must be sorted and unique")
    runtime_descriptor = 10 * len(callable_services)
    runtime = (len(code) + runtime_descriptor + 0xFF) & ~0xFF
    allocation = runtime if allocation is None else allocation
    if (not code or entry_offset >= len(code) or allocation < len(code)
            or allocation & 0xFF):
        raise SystemExit("invalid RSX code, entry, or allocation")
    if allocation < len(code) + runtime_descriptor:
        raise SystemExit("RSX allocation cannot hold runtime service descriptors")
    if format_version == 2 and (entry_offset < 8 or any(
            service[3] < 8 or service[3] >= len(code)
            for service in callable_services)):
        raise SystemExit("BRSX v2 entry overlaps its runtime header or payload end")
    for label, offset in (("initialization", init_offset),
                          ("shutdown", shutdown_offset)):
        if offset != NO_ENTRY and offset >= len(code):
            raise SystemExit(f"invalid RSX {label} entry")
    if len(set(relocations)) != len(relocations) or any(
            offset < 0 or offset + 1 >= len(code) for offset in relocations):
        raise SystemExit("invalid or duplicate RSX relocation offset")
    if any(offset in (0, 2) or offset < 0 or offset + 1 >= len(code)
           for offset in runtime_pointers):
        raise SystemExit("invalid loader-owned or out-of-range runtime pointer slot")
    if RELOCATION_OFFSET + 2 * len(relocations) > HEADER_SIZE:
        raise SystemExit("RSX relocation directory exceeds its header")
    metadata_offset = HEADER_SIZE + len(code)
    metadata = (bytes(services) if format_version == 1 else
                _v2_metadata(services, callable_services, runtime_pointers))
    header = bytearray(HEADER_SIZE)
    primary = services[0] if services else 0xFFFF
    flags = flags | RECONSTRUCTION_CLASSES[reconstruction_class]
    struct.pack_into("<4sBBBBHHHHHHHHHHHH8sBBBBHH", header, 0,
                     MAGIC, format_version, 2, 1, 0, flags, linked_base, len(code), allocation,
                     entry_offset, init_offset, shutdown_offset, len(relocations),
                     HEADER_SIZE, HEADER_SIZE, RELOCATION_OFFSET, metadata_offset,
                     stem.ljust(8, b" "), version[0], version[1], len(services), 0,
                     sum(code) & 0xFFFF, primary)
    for index, offset in enumerate(relocations):
        struct.pack_into("<H", header, RELOCATION_OFFSET + index * 2, offset)
    return bytes(header) + code + metadata
