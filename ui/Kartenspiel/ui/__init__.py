def main() -> None:
    try:
        from .anwendung import Anwendung
    except ModuleNotFoundError as fehler:
        if fehler.name != "pygame":
            raise
        raise SystemExit(
            "Für die Oberfläche im ui-Ordner zuerst installieren: python3 -m pip install ."
        ) from None
    Anwendung().laufen()
