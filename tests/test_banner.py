from io import StringIO
import importlib

import fyron
from fyron.banner import BF_FYRON_ASCII, get_run_footer, get_run_header


def test_banner_contains_bits_flames_and_fyron():
    banner = fyron.get_banner(version="1.2.3", color=False)

    assert BF_FYRON_ASCII in banner
    assert "Bits & Flames - Fyron" in banner
    assert "Fyron" in banner
    assert "version 1.2.3" in banner
    assert "\033[" not in banner
    assert all(ord(character) < 128 for character in banner)


def test_colored_banner_uses_ansi_colors():
    banner = fyron.get_banner(version="1.2.3")

    assert "\033[" in banner
    assert "Bits & Flames" in banner
    assert "Fyron" in banner


def test_print_banner_writes_to_file_like_object():
    output = StringIO()

    fyron.print_banner(version="1.2.3", color=False, file=output)

    assert "Bits & Flames - Fyron" in output.getvalue()
    assert "version 1.2.3" in output.getvalue()


def test_banner_themes_and_run_summary_are_available():
    mono = fyron.get_banner(version="1.2.3", color=False, theme="mono")
    header = get_run_header("docs-build", color=False)
    footer = get_run_footer(duration=1.25, outputs=["site"], color=False)

    assert "FYRON" in mono
    assert "docs-build" in header
    assert "version" in header
    assert "duration 1.25s" in footer
    assert "site" in footer


def test_import_fyron_does_not_print_banner(capsys):
    importlib.reload(fyron)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
