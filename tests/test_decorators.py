import json
from pathlib import Path
from typing import Dict
from typing import List

import pandas as pd
from _pytest.monkeypatch import MonkeyPatch

from src.utils.decorators import save_report


def test_save_report_dataframe(tmp_path: Path) -> None:
    """Декоратор сохраняет DataFrame в JSON."""
    file_path = tmp_path / "report.json"

    @save_report(str(file_path))
    def make_report() -> pd.DataFrame:
        return pd.DataFrame({"category": ["Еда"], "amount": [100]})

    result = make_report()

    assert file_path.exists()
    assert isinstance(result, pd.DataFrame)
    assert json.loads(file_path.read_text(encoding="utf-8")) == [{"category": "Еда", "amount": 100}]


def test_save_report_dict(tmp_path: Path) -> None:
    """Декоратор сохраняет обычные данные в JSON."""
    file_path = tmp_path / "report.json"

    @save_report(str(file_path))
    def make_report() -> Dict[str, int]:
        return {"amount": 100}

    result = make_report()

    assert file_path.exists()
    assert result == {"amount": 100}
    assert json.loads(file_path.read_text(encoding="utf-8")) == {"amount": 100}


def test_save_report_auto_filename(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Декоратор создаёт файл с автоименем."""
    monkeypatch.chdir(tmp_path)

    @save_report()
    def auto_report() -> List[Dict[str, int]]:
        return [{"amount": 100}]

    auto_report()

    files = list((tmp_path / "reports").glob("auto_report_*.json"))

    assert len(files) == 1
    assert json.loads(files[0].read_text(encoding="utf-8")) == [{"amount": 100}]
