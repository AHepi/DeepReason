"""Internal resource and network containment wrapper for verifier commands."""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import errno
import os
import resource
import sys

_ABORT_PREFIX = "DEEPREASON_SANDBOX_ABORT:"
_SCMP_ACT_ALLOW = 0x7FFF0000
_SCMP_ACT_ERRNO = 0x00050000


def seccomp_available() -> bool:
    return sys.platform.startswith("linux") and ctypes.util.find_library("seccomp") is not None


def _deny_network() -> None:
    library_name = ctypes.util.find_library("seccomp")
    if not library_name:
        raise RuntimeError("libseccomp unavailable")
    seccomp = ctypes.CDLL(library_name, use_errno=True)
    seccomp.seccomp_init.argtypes = [ctypes.c_uint32]
    seccomp.seccomp_init.restype = ctypes.c_void_p
    seccomp.seccomp_rule_add.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_uint,
    ]
    seccomp.seccomp_rule_add.restype = ctypes.c_int
    seccomp.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    seccomp.seccomp_syscall_resolve_name.restype = ctypes.c_int
    seccomp.seccomp_load.argtypes = [ctypes.c_void_p]
    seccomp.seccomp_load.restype = ctypes.c_int
    seccomp.seccomp_release.argtypes = [ctypes.c_void_p]

    context = seccomp.seccomp_init(_SCMP_ACT_ALLOW)
    if not context:
        raise RuntimeError("seccomp_init failed")
    try:
        deny = _SCMP_ACT_ERRNO | errno.EPERM
        for syscall in (
            b"socket",
            b"socketpair",
            b"connect",
            b"accept",
            b"accept4",
            b"bind",
            b"listen",
            b"sendto",
            b"sendmsg",
            b"recvfrom",
            b"recvmsg",
            b"sendmmsg",
            b"recvmmsg",
            b"socketcall",
        ):
            number = seccomp.seccomp_syscall_resolve_name(syscall)
            if number >= 0 and seccomp.seccomp_rule_add(context, deny, number, 0) != 0:
                raise RuntimeError(f"could not block {syscall.decode()}")
        if seccomp.seccomp_load(context) != 0:
            raise RuntimeError("seccomp_load failed")
    finally:
        seccomp.seccomp_release(context)


def _limit(kind: int, value: int) -> None:
    _soft, hard = resource.getrlimit(kind)
    bounded = value if hard == resource.RLIM_INFINITY else min(value, hard)
    resource.setrlimit(kind, (bounded, bounded))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--cpu-seconds", type=int, required=True)
    parser.add_argument("--memory-bytes", type=int, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        return 126
    try:
        _limit(resource.RLIMIT_CPU, args.cpu_seconds)
        _limit(resource.RLIMIT_AS, args.memory_bytes)
        _deny_network()
        os.execve(command[0], command, os.environ)
    except BaseException as error:  # noqa: BLE001 - last boundary before exec
        sys.stderr.write(f"{_ABORT_PREFIX}{type(error).__name__}:{error}\n")
        return 126
    return 126


if __name__ == "__main__":  # pragma: no cover - exercised by the Lean backend
    raise SystemExit(main())
