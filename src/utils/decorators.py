import json
import os
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


def save_report(filename: Optional[str] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Декоратор сохраняющий результат функции в JSON файл."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            report_filename = filename

            if report_filename is None:
                report_name = func.__name__
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_filename = f"reports/{report_name}_{timestamp}.json"

            os.makedirs(os.path.dirname(report_filename), exist_ok=True)

            result: T = func(*args, **kwargs)

            with open(report_filename, "w", encoding="utf-8") as f:
                data = result.to_dict(orient="records") if hasattr(result, "to_dict") else result
                json.dump(data, f, ensure_ascii=False, indent=2)

            return result

        return wrapper

    return decorator
