import os
import sys
import threading
import time
import traceback


class Logger:
    def __init__(self, file_path: str):
        self.file_path = file_path
        folder = os.path.dirname(self.file_path) or os.getcwd()
        os.makedirs(folder, exist_ok=True)
        self._lock = threading.Lock()

    def _format(self, msg: str, args) -> str:
        if args:
            try:
                return msg % args
            except Exception:
                return msg + " " + " ".join([repr(x) for x in args])
        return msg

    def _write(self, level: str, txt: str) -> None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        line = f"{ts} {level} {txt}\n"
        with self._lock:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(line)

    def debug(self, msg: str, *args, **kwargs) -> None:
        self._write("DEBUG", self._format(msg, args))

    def info(self, msg: str, *args, **kwargs) -> None:
        self._write("INFO", self._format(msg, args))

    def warning(self, msg: str, *args, **kwargs) -> None:
        self._write("WARNING", self._format(msg, args))

    def error(self, msg: str, *args, **kwargs) -> None:
        self._write("ERROR", self._format(msg, args))

    def exception(self, msg: str, *args, **kwargs) -> None:
        exc = sys.exc_info()
        base = self._format(msg, args)
        if exc[0] is None:
            self._write("EXCEPTION", base)
            return
        tb = "".join(traceback.format_exception(*exc)).rstrip()
        self._write("EXCEPTION", base + "\n" + tb)
