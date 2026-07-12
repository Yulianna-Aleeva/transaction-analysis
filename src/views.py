from typing import Any, Dict, List

import pandas as pd

from src.api.api_currency import get_currency_rates
from src.api.api_stocks import get_stock_prices
from src.logs.log_config import get_logger
from src.utils.format_utils import greeting_time

logger = get_logger(__name__)


def get_cards_info(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Считает по картам: последние 4 цифры, расходы и кешбэк (1%)."""
    expenses = df[df["amount_operation"] < 0].copy()
    if expenses.empty or "card_number" not in expenses.columns:
        return []

    grouped = expenses.groupby("card_number")["amount_operation"].sum().reset_index()

    result = []
    for _, row in grouped.iterrows():
        card_raw = str(row["card_number"]).replace("*", "").strip()
        last_digits = card_raw[-4:] if card_raw else "0000"

        total_spent = round(abs(row["amount_operation"]), 2)
        cashback = round(total_spent / 100, 2)

        result.append(
            {
                "last_digits": last_digits,
                "total_spent": total_spent,
                "cashback": cashback,
            }
        )

    logger.debug("Собрана информация по %s картам.", len(result))
    return result


def get_main_page_data(date_str: str, df: pd.DataFrame, use_last_date: bool = False) -> Dict[str, Any]:
    """Формирует JSON для главной страницы с начала месяца по входящую дату."""
    try:
        # Выбор режима определения конечной даты
        if use_last_date:
            end_date = df["date_operation"].max()
            end_date = pd.Timestamp(end_date).replace(hour=23, minute=59, second=59)
        else:
            end_date = pd.to_datetime(date_str, format="%Y-%m-%d %H:%M:%S", errors="coerce")
            if pd.isna(end_date):
                end_date = pd.Timestamp.now()

        start_date = end_date.replace(day=1, hour=0, minute=0, second=0)

        mask = (df["date_operation"] >= start_date) & (df["date_operation"] <= end_date)
        df_period_raw = df.loc[mask].copy()
        if not isinstance(df_period_raw, pd.DataFrame):
            logger.warning("Фильтр вернул не DataFrame, возвращаем пустой DataFrame")
            df_period = pd.DataFrame(columns=df.columns)
        else:
            df_period = df_period_raw

        # Топ-5 транзакций
        top_5 = df_period.sort_values("amount_operation", ascending=False).head(5).copy()
        top_5["date"] = top_5["date_operation"].dt.strftime("%d.%m.%Y")
        top_transactions = (
            top_5[["date", "amount_operation", "category", "description"]]
            .rename(columns={"amount_operation": "amount"})
            .to_dict(orient="records")
        )

        result = {
            "greeting": greeting_time(),
            "cards": get_cards_info(df_period),
            "top_transactions": top_transactions,
            "currency_rates": get_currency_rates(),
            "stock_prices": get_stock_prices(),
        }

        logger.debug("Данные главной страницы сформированы для периода %s — %s", start_date, end_date)
        return result

    except Exception as e:
        logger.error("Ошибка формирования главной страницы: %s", e, exc_info=True)
        return {"error": str(e)}


def get_events_page_data(date_str: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Формирует JSON для страницы «События»:
    - расходы с ТОП-7 категориями и «Остальное»
    - выделенные переводы и наличные
    - поступления
    - курсы валют и акций
    """
    try:
        end_date = pd.to_datetime(date_str, format="%Y-%m-%d %H:%M:%S", errors="coerce")
        if pd.isna(end_date):
            end_date = df["date_operation"].max()

        start_date = end_date.replace(day=1, hour=0, minute=0, second=0)
        mask = (df["date_operation"] >= start_date) & (df["date_operation"] <= end_date)
        period = df.loc[mask].copy()

        # === Расходы ===
        expenses_df = period[period["amount_operation"] < 0].copy()
        total_expenses = int(abs(expenses_df["amount_operation"].sum()))

        # Группировка по категориям
        cat_sum = expenses_df.groupby("category")["amount_operation"].sum().abs().sort_values(ascending=False)

        # Топ-7
        top7 = cat_sum.head(7).reset_index()
        top7.columns = ["category", "amount"]
        top7["amount"] = top7["amount"].astype(int)
        top7_list = top7.to_dict(orient="records")

        # Остальное
        if len(cat_sum) > 7:
            rest_amount = int(cat_sum.iloc[7:].sum())
            top7_list.append({"category": "Остальное", "amount": rest_amount})

        # Переводы и наличные
        transfers_cash = expenses_df[expenses_df["category"].isin(["Наличные", "Переводы"])]
        transfers_cash_sum = (
            transfers_cash.groupby("category")["amount_operation"]
            .sum()
            .abs()
            .astype(int)
            .reset_index()
            .rename(columns={"amount_operation": "amount"})
            .to_dict(orient="records")
        )

        # === Поступления ===
        income_df = period[period["amount_operation"] > 0].copy()
        total_income = int(income_df["amount_operation"].sum())

        income_cat = (
            income_df.groupby("category")["amount_operation"]
            .sum()
            .astype(int)
            .sort_values(ascending=False)
            .reset_index()
            .rename(columns={"amount_operation": "amount"})
            .to_dict(orient="records")
        )

        result = {
            "expenses": {
                "total_amount": total_expenses,
                "main": top7_list,
                "transfers_and_cash": transfers_cash_sum,
            },
            "income": {
                "total_amount": total_income,
                "main": income_cat,
            },
            "currency_rates": get_currency_rates(),
            "stock_prices": get_stock_prices(),
        }

        logger.debug('Данные страницы "События" сформированы за %s — %s', start_date, end_date)
        return result

    except Exception as e:
        logger.error('Ошибка формирования страницы "События": %s', e, exc_info=True)
        return {"error": str(e)}
