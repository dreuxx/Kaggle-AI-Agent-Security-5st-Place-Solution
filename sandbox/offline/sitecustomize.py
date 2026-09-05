"""Deny Python IPv4/IPv6 network access inside the local experiment sandbox."""

from __future__ import annotations

import errno
import socket
from typing import Any


class SandboxNetworkDisabled(PermissionError):
    """Raised when sandboxed Python code attempts IP network access."""


_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex
_original_sendto = socket.socket.sendto


def _denied(operation: str) -> SandboxNetworkDisabled:
    return SandboxNetworkDisabled(
        errno.EPERM,
        f"Red IPv4/IPv6 deshabilitada por el sandbox: {operation}",
    )


def _guarded_connect(self: socket.socket, address: Any) -> Any:
    if self.family in (socket.AF_INET, socket.AF_INET6):
        raise _denied("socket.connect")
    return _original_connect(self, address)


def _guarded_connect_ex(self: socket.socket, address: Any) -> int:
    if self.family in (socket.AF_INET, socket.AF_INET6):
        return errno.EPERM
    return _original_connect_ex(self, address)


def _guarded_sendto(self: socket.socket, data: bytes, *args: Any) -> int:
    if self.family in (socket.AF_INET, socket.AF_INET6):
        raise _denied("socket.sendto")
    return _original_sendto(self, data, *args)


def _blocked_create_connection(*args: Any, **kwargs: Any) -> socket.socket:
    raise _denied("socket.create_connection")


def _blocked_getaddrinfo(*args: Any, **kwargs: Any) -> list[Any]:
    raise _denied("socket.getaddrinfo")


socket.socket.connect = _guarded_connect
socket.socket.connect_ex = _guarded_connect_ex
socket.socket.sendto = _guarded_sendto
socket.create_connection = _blocked_create_connection
socket.getaddrinfo = _blocked_getaddrinfo
