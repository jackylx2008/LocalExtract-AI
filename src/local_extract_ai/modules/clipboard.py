"""Windows 剪贴板图片读取与文本写入。"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass

from PIL import Image, ImageGrab


class ClipboardError(RuntimeError):
    """剪贴板内容或访问异常。"""


@dataclass(frozen=True, slots=True)
class ClipboardImage:
    png_bytes: bytes
    width: int
    height: int


def read_image() -> ClipboardImage:
    """读取剪贴板中的位图并编码为 PNG。"""
    content = ImageGrab.grabclipboard()
    if not isinstance(content, Image.Image):
        raise ClipboardError("剪贴板中没有截图，请先复制一张图片")
    image = content.convert("RGB")
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return ClipboardImage(stream.getvalue(), image.width, image.height)


def write_text(text: str) -> None:
    """使用 Win32 API 将 Unicode 文本写入剪贴板。"""
    if os.name != "nt":
        raise ClipboardError("写入系统剪贴板仅支持 Windows")
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE

    if not user32.OpenClipboard(None):
        raise ClipboardError("无法打开剪贴板，请稍后重试")
    handle = None
    try:
        if not user32.EmptyClipboard():
            raise ClipboardError("无法清空剪贴板")
        encoded = (text + "\0").encode("utf-16-le")
        handle = kernel32.GlobalAlloc(0x0002, len(encoded))
        if not handle:
            raise ClipboardError("无法分配剪贴板内存")
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            raise ClipboardError("无法锁定剪贴板内存")
        try:
            ctypes.memmove(pointer, encoded, len(encoded))
        finally:
            kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(13, handle):
            raise ClipboardError("无法写入剪贴板")
        handle = None  # 所有权已经转移给系统。
    finally:
        user32.CloseClipboard()
        if handle:
            kernel32.GlobalFree(handle)
