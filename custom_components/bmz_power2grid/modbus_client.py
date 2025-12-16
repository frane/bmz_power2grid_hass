from __future__ import annotations

import asyncio
import socket
import struct
from dataclasses import dataclass
from typing import Sequence

def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    return crc & 0xFFFF

@dataclass
class RtuOverTcpClient:
    host: str
    port: int
    timeout: float = 3.0

    async def read_holding_registers(self, unit: int, address: int, count: int) -> list[int]:
        # Build RTU frame: [unit][func=0x03][addrHi addrLo][countHi countLo][crcLo crcHi]
        func = 0x03
        pdu = struct.pack(">B B H H", unit, func, address, count)
        frame = pdu + struct.pack("<H", crc16_modbus(pdu))

        def _io() -> bytes:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as s:
                s.sendall(frame)
                # Read enough. Server responses are tiny.
                return s.recv(4096)

        resp = await asyncio.to_thread(_io)
        if len(resp) < 5:
            raise IOError(f"Short response ({len(resp)} bytes)")

        # Basic parse: [unit][func][bytecount][data...][crc]
        if resp[0] != unit:
            raise IOError(f"Unit mismatch: got {resp[0]} expected {unit}")
        if resp[1] & 0x80:
            exc = resp[2]
            raise IOError(f"Modbus exception {exc:#02x}")
        if resp[1] != func:
            raise IOError(f"Function mismatch: got {resp[1]} expected {func}")

        bytecount = resp[2]
        data = resp[3:3 + bytecount]
        if len(data) != bytecount:
            raise IOError("Truncated payload")

        regs = [int.from_bytes(data[i:i+2], "big") for i in range(0, len(data), 2)]
        return regs

def regs_to_s32_be(regs: Sequence[int]) -> int:
    """Big-endian pair (hi, lo), signed 32-bit."""
    if len(regs) < 2:
        raise ValueError("Need 2 registers")
    b = regs[0].to_bytes(2, "big") + regs[1].to_bytes(2, "big")
    return int.from_bytes(b, "big", signed=True)


def regs_to_u32_be(regs: Sequence[int]) -> int:
    """Big-endian pair (hi, lo), unsigned 32-bit."""
    if len(regs) < 2:
        raise ValueError("Need 2 registers")
    b = regs[0].to_bytes(2, "big") + regs[1].to_bytes(2, "big")
    return int.from_bytes(b, "big", signed=False)


def regs_to_s16(reg: int) -> int:
    """Convert unsigned 16-bit register to signed 16-bit."""
    if reg >= 0x8000:
        return reg - 0x10000
    return reg