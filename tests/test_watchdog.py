import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "client"))

from rtlsdr_usbip_watchdog import UsbipError, find_rtlsdr_busid, is_attached  # noqa: E402


USBIP_LIST_OUTPUT = """\
- 192.168.1.50
        1-1.4: unknown vendor : unknown product (0bda:2838)
           : /sys/devices/pci0000:00/.../usb1/1-1/1-1.4
           : (Defined at Interface level) (00/00/00)

 - busid 1-1.4 (0bda:2838)
   Realtek Semiconductor Corp. : RTL2838 DVB-T
"""

USBIP_LIST_NO_RTLSDR = """\
- 192.168.1.50
 - busid 1-1.2 (046d:c52b)
   Logitech, Inc. : Unifying Receiver
"""

USBIP_LIST_MULTIPLE = """\
- 192.168.1.50
 - busid 1-1.2 (046d:c52b)
   Logitech, Inc. : Unifying Receiver

 - busid 1-1.4 (0bda:2838)
   Realtek Semiconductor Corp. : RTL2838 DVB-T

 - busid 1-1.5 (0bda:2832)
   Realtek Semiconductor Corp. : RTL2832U
"""


def test_find_rtlsdr_busid_matches_known_device():
    assert find_rtlsdr_busid(USBIP_LIST_OUTPUT) == "1-1.4"


def test_find_rtlsdr_busid_raises_when_absent():
    with pytest.raises(UsbipError):
        find_rtlsdr_busid(USBIP_LIST_NO_RTLSDR)


def test_find_rtlsdr_busid_picks_first_match_when_multiple():
    assert find_rtlsdr_busid(USBIP_LIST_MULTIPLE) == "1-1.4"


def test_is_attached_true_when_port_line_present(monkeypatch):
    def fake_run_usbip(*args):
        assert args == ("port",)

        class Result:
            returncode = 0
            stdout = (
                "Imported USB devices\n"
                "====================\n"
                "Port 00: <Port in Use> at Full Speed(12Mbps)\n"
                "       unknown vendor : unknown product (0bda:2838)\n"
                "       -> usbip://192.168.1.50:3240/1-1.4\n"
                "       -> remote bus/dev 001/004\n"
            )
            stderr = ""

        return Result()

    import rtlsdr_usbip_watchdog as mod

    monkeypatch.setattr(mod, "run_usbip", fake_run_usbip)
    assert is_attached("192.168.1.50", "1-1.4") is True


def test_is_attached_false_when_no_matching_port(monkeypatch):
    def fake_run_usbip(*args):
        class Result:
            returncode = 0
            stdout = "Imported USB devices\n====================\n"
            stderr = ""

        return Result()

    import rtlsdr_usbip_watchdog as mod

    monkeypatch.setattr(mod, "run_usbip", fake_run_usbip)
    assert is_attached("192.168.1.50", "1-1.4") is False
