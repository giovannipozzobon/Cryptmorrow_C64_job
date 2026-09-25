"""Drive a private VICE through its binary and text monitors.

Only the VICE process started here is controlled and closed.
Protocol reference: https://vice-emu.sourceforge.io/vice_13.html
Works with VICE 3.7 (Linux, headless under xvfb-run) and 3.10 (Windows).
"""
import hashlib
from pathlib import Path
import re
import shutil
import socket
import struct
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
# VICE's C64, x64sc, from the PATH; --vice gives another one.
DEFAULT_VICE = Path(shutil.which("x64sc") or "x64sc")
PAL_LINE_CYCLES = 63
PAL_FRAME_CYCLES = 312 * PAL_LINE_CYCLES     # 19656


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def note(message):
    print(message, file=sys.stderr, flush=True)


def load_labels(path):
    text = Path(path).read_text(encoding="utf-8")
    return {match[2]: int(match[1], 16) for match in re.finditer(
        r"al\s+([0-9a-fA-F]+)\s+\.(\w+)", text)}


def free_port():
    with socket.socket() as reserve:
        reserve.bind(("127.0.0.1", 0))
        return reserve.getsockname()[1]


class Monitor:
    def __init__(self, connection):
        self.connection = connection
        self.request_id = 0
        self.events = []
        self.bank = None
        self.registers = {}

    def read(self, count):
        parts = bytearray()
        while len(parts) < count:
            part = self.connection.recv(count - len(parts))
            require(bool(part), "VICE disconnected unexpectedly")
            parts.extend(part)
        return bytes(parts)

    def response(self):
        header = self.read(12)
        require(header[:2] == b"\x02\x02", "Unexpected VICE monitor header")
        length, kind, error, request_id = struct.unpack("<IBBI", header[2:])
        body = self.read(length)
        require(error == 0, f"VICE error {error:#x}, response {kind:#x}")
        return kind, request_id, body

    def command(self, kind, body=b""):
        self.request_id += 1
        packet = b"\x02\x02" + struct.pack("<IIB", len(body),
                                           self.request_id, kind)
        self.connection.sendall(packet + body)
        while True:
            try:
                answer_kind, request_id, answer = self.response()
            except TimeoutError as error:
                raise RuntimeError(
                    f"Timed out waiting for VICE command {kind:#04x}"
                ) from error
            if request_id == self.request_id:
                return answer
            self.events.append((answer_kind, answer))

    def setup(self):
        self.command(0x81)                          # ping
        banks = self.command(0x82)
        position, mapping = 2, {}
        for _ in range(struct.unpack("<H", banks[:2])[0]):
            size = banks[position]
            bank_id, length = struct.unpack(
                "<HB", banks[position + 1:position + 4])
            mapping[banks[position + 4:position + 4 + length].decode()] = \
                bank_id
            position += size + 1
        require("cpu" in mapping, "VICE did not expose the CPU bank")
        self.bank = mapping["cpu"]
        names = self.command(0x83, b"\x00")
        position = 2
        for _ in range(struct.unpack("<H", names[:2])[0]):
            size = names[position]
            reg_id, _, length = struct.unpack(
                "<BBB", names[position + 1:position + 4])
            name = names[position + 4:position + 4 + length].decode()
            self.registers[name] = reg_id
            position += size + 1
        for name in ("PC", "01", "LIN", "CYC"):
            require(name in self.registers, f"VICE lacks register {name}")

    def memory(self, address, count):
        body = struct.pack("<BHHBH", 0, address, address + count - 1, 0,
                           self.bank)
        answer = self.command(0x01, body)
        require(struct.unpack("<H", answer[:2])[0] == count, "Short read")
        return answer[2:2 + count]

    def poke(self, address, data):
        body = struct.pack("<BHHBH", 0, address, address + len(data) - 1,
                           0, self.bank) + data
        self.command(0x02, body)

    def read_registers(self):
        answer = self.command(0x31, b"\x00")
        names = {v: k for k, v in self.registers.items()}
        values, position = {}, 2
        for _ in range(struct.unpack("<H", answer[:2])[0]):
            size = answer[position]
            reg_id = answer[position + 1]
            value = struct.unpack("<H", answer[position + 2:position + 4])[0]
            values[names.get(reg_id, reg_id)] = value
            position += size + 1
        return values

    def set_pc(self, address):
        body = struct.pack("<BH", 0, 1) + \
            struct.pack("<BBH", 3, self.registers["PC"], address)
        self.command(0x32, body)

    def checkpoint(self, address):
        """Stop when `address` is executed; returns the number."""
        answer = self.command(0x12, struct.pack(
            "<HHBBBBB", address, address, 1, 1, 4, 0, 0))
        return struct.unpack("<I", answer[:4])[0]

    def delete_checkpoint(self, number):
        self.command(0x13, struct.pack("<I", number))

    def run_until_stop(self):
        """Resume and wait for the next checkpoint; return its PC."""
        self.events = []
        self.command(0xAA)
        while True:
            for kind, body in self.events:
                if kind == 0x62:                    # stopped
                    return struct.unpack("<H", body[:2])[0]
            try:
                kind, _, body = self.response()
            except TimeoutError as error:
                raise RuntimeError("Timed out waiting for a checkpoint") \
                    from error
            self.events.append((kind, body))

    def run_to(self, address):
        for _ in range(64):
            if self.run_until_stop() == address:
                return
        raise RuntimeError(f"VICE did not stop at {address:#06x}")

    def raster_time(self):
        """Cycles since the start of the current PAL frame."""
        registers = self.read_registers()
        return registers["LIN"] * PAL_LINE_CYCLES + registers["CYC"]


class Vice:
    """Starts x64sc hidden, with both monitors on private ports."""

    def __init__(self, vice, prg, log_path, evidence="evidence"):
        """evidence: the folder of the screenshots, relative to the
        project (VICE runs there)."""
        self.evidence = evidence
        self.port, self.text_port = free_port(), free_port()
        while self.text_port == self.port:
            self.text_port = free_port()
        startup = None
        if sys.platform == "win32":
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
        self.log = open(log_path, "w", encoding="utf-8")
        self.process = subprocess.Popen([
            str(vice), "-default", "-pal", "+sound", "-warp",
            "+VICIIvcache", "-autostartprgmode", "1",
            "-binarymonitor", "-binarymonitoraddress",
            f"127.0.0.1:{self.port}", "-remotemonitor",
            "-remotemonitoraddress", f"127.0.0.1:{self.text_port}",
            "-autostart", str(prg)], cwd=PROJECT, startupinfo=startup,
            stdout=self.log, stderr=subprocess.STDOUT)
        self.connection = None

    def connect(self, settle):
        deadline = time.monotonic() + 30
        while self.connection is None:
            require(self.process.poll() is None,
                    "VICE exited before its monitor was ready")
            try:
                self.connection = socket.create_connection(
                    ("127.0.0.1", self.port), timeout=1)
            except OSError:
                require(time.monotonic() < deadline,
                        "Timed out starting VICE's monitor")
                time.sleep(0.1)
        self.connection.settimeout(30)
        time.sleep(settle)          # let autostart load and run the PRG
        monitor = Monitor(self.connection)
        monitor.setup()
        return monitor

    def screenshot(self, name):
        """Native PNG export through the text monitor."""
        output = PROJECT / self.evidence / name
        if output.exists():
            output.unlink()
        with socket.create_connection(("127.0.0.1", self.text_port),
                                      timeout=5) as remote:
            remote.sendall(f'screenshot "{self.evidence}/{name}" 2\n'
                           .encode())
            answer = bytearray()
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                try:
                    chunk = remote.recv(4096)
                    if chunk:
                        answer.extend(chunk)
                except (TimeoutError, OSError):
                    pass
                require(b"ERROR" not in answer.upper(),
                        f"VICE screenshot failed: {answer!r}")
                if b"(C:$" in answer or (output.exists() and
                                          output.stat().st_size > 1000):
                    break
        time.sleep(0.5)
        require(output.exists(), f"VICE did not write {output}")
        data = output.read_bytes()
        require(data[:8] == b"\x89PNG\r\n\x1a\n", f"Not a PNG: {output}")
        size = struct.unpack(">II", data[16:24])
        require(size == (384, 272), f"Unexpected screenshot size {size}")
        return {"file": f"{self.evidence}/{name}", "width": size[0],
                "height": size[1],
                "sha256": hashlib.sha256(data).hexdigest()}

    def close(self):
        if self.connection is not None:
            self.connection.close()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.log.close()
