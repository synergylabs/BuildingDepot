# vendored deploy library — do not edit here; regenerate from the deploy source.
"""Ask the operator a question, or wait for them to acknowledge something.

Deliberately not clever: there is no attempt to detect whether a human is present.
Prompts always show, and `--yes` (`set_yes(True)`) is the only thing that suppresses
them. Run a prompting script through a pipe without `--yes` and it raises EOFError,
which is the wanted outcome — better a loud crash than silently assuming an answer
nobody gave.

Both the question and the answer go through `/dev/tty` rather than stdin/stdout, for
two reasons:

  * `proc.run(capture=False)` lets child processes inherit stdin, so an installer
    that reads stdin would otherwise swallow the next prompt.
  * `transcript` redirects fd 1 and 2 into a line-buffered pipe, so a question
    written there would not appear until its trailing newline — i.e. never, since a
    question ends without one.

That also means prompts do not appear in the transcript. Callers that want the
question on the record should log it as well as ask it.
"""

from __future__ import annotations

from typing import IO

_yes: bool = False
_tty_in: IO[str] | None = None
_tty_out: IO[str] | None = None


def set_yes(value: bool) -> None:
    """Answer every subsequent prompt affirmatively and skip every pause."""
    global _yes
    _yes = value


def _streams() -> tuple[IO[str], IO[str]]:
    """The terminal, as a read handle and a write handle.

    Two handles rather than one opened "r+": a buffered text stream has to be
    seekable to be readable *and* writable, and a tty is not, so "r+" raises
    io.UnsupportedOperation on the first read.

    No fallback to stdin/stdout — if there is no controlling terminal then there is
    nobody to ask, and --yes is the documented way to say so.
    """
    global _tty_in, _tty_out
    if _tty_in is None or _tty_out is None:
        _tty_in = open("/dev/tty", "r", encoding="utf-8")
        _tty_out = open("/dev/tty", "w", encoding="utf-8")
    return _tty_in, _tty_out


def _ask(question: str) -> str:
    reader, writer = _streams()
    writer.write(question)
    writer.flush()
    line = reader.readline()
    if not line:
        raise EOFError(f"no answer available for: {question.strip()}")
    return line.strip()


def confirm(question: str) -> bool:
    """Ask a yes/no question, returning True only on an explicit yes.

    Anything other than y/yes is a no, so a stray keypress never counts as consent.
    """
    if _yes:
        return True
    return _ask(f"    {question} [y/N] ").lower() in ("y", "yes")


def pause(message: str = "press Enter to continue, Ctrl-C to stop") -> None:
    """Block until the operator acknowledges."""
    if _yes:
        return
    _ask(f"    {message} ")
