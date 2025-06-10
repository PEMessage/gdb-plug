#Thanks to: https://github.com/prompt-toolkit/ptpython/issues/546
import sys

import gdb
from ptpython import embed


class PtPythonCommand(gdb.Command):
    def __init__(self) -> None:
        super().__init__("ptpython", gdb.COMMAND_USER)

    def invoke(self, arg: str, from_tty: bool):
        self.dont_repeat()

        if not from_tty:
            raise Exception("PtPython can only be launched from the TTY")

        stdout = sys.stdout
        stderr = sys.stderr
        stdin = sys.stdin

        try:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            sys.stdin = sys.__stdin__

            embed()

        except SystemExit as e:
            if e.code != 0:
                print("ptpython exited with code", e.code)

        finally:
            sys.stdout = stdout
            sys.stderr = stderr
            sys.stdin = stdin


PtPythonCommand()

