import pandas as pd


def load_transactions(file_path: str) -> pd.DataFrame:
    """Загружает данные из Excel-файла в объект DataFrame."""
    try:
        df = pd.read_excel(file_path)
        print(f"Загружено строк: {len(df)}.")
        return df
    except FileNotFoundError as e:
        print(f"❌ Ошибка: Файл не найден. Проверьте путь к {file_path}.")
        raise e


def sort_transactions_by_amount(df: pd.DataFrame) -> pd.DataFrame:
    """Сортирует транзакции по убыванию суммы."""
    return df.sort_values(by="Сумма операции", ascending=False).copy()


def format_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Преобразует столбец "Дата операции" в формат "dd.mm.yyyy"."""
    df = df.copy()

    df["date"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)
    df["date"] = df["date"].dt.strftime("%d.%m.%Y")

    return df
