from typing import Any
from typing import Dict
from typing import List
from typing import cast

import pandas as pd

from src.api.api_currency import get_currency_rates
from src.api.api_stocks import get_stock_prices
from src.log_config import get_logger
from src.utils.format_utils import greeting_time

logger = get_logger(__name__)


def get_main_page_data(date_str: str, df: pd.DataFrame, use_last_date: bool = False) -> Dict[str, Any]:
    """Формирует JSON для главной страницы с начала месяца по входящую дату."""
    try:
        if use_last_date:
            end_date = df["date_operation"].max()
            end_date = pd.Timestamp(end_date).replace(hour=23, minute=59, second=59)
        else:
            end_date = pd.to_datetime(date_str, format="%Y-%m-%d %H:%M:%S", errors="coerce")
            if pd.isna(end_date):
                end_date = pd.Timestamp.now()

        start_date = end_date.replace(day=1, hour=0, minute=0, second=0)

        mask = (df["date_operation"] >= start_date) & (df["date_operation"] <= end_date)
        period = cast(pd.DataFrame, df.loc[mask].copy())

        top_5 = period.sort_values("amount_rub", ascending=False).head(5).copy()
        top_5["date"] = top_5["date_operation"].dt.strftime("%d.%m.%Y")
        top_5["amount"] = top_5["amount_rub"].abs().round(0).astype(int)

        top_transactions = top_5[["date", "amount", "category", "description"]].to_dict(orient="records")

        result = {
            "greeting": greeting_time(),
            "cards": get_cards_info(period),
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
    """Формирует JSON для страницы «События»."""
    try:
        end_date = pd.to_datetime(date_str, format="%Y-%m-%d %H:%M:%S", errors="coerce")
        if pd.isna(end_date):
            end_date = df["date_operation"].max()

        start_date = end_date.replace(day=1, hour=0, minute=0, second=0)
        mask = (df["date_operation"] >= start_date) & (df["date_operation"] <= end_date)
        period = cast(pd.DataFrame, df.loc[mask].copy())

        # === Расходы ===
        expenses_df = period[period["amount_rub"] < 0].copy()
        total_expenses = int(abs(expenses_df["amount_rub"].sum()))

        cat_sum = expenses_df.groupby("category")["amount_rub"].sum().abs().sort_values(ascending=False)
        cat_sum = cat_sum.round(0).astype(int)

        top7 = cat_sum.head(7).reset_index()
        top7.columns = ["category", "amount"]
        top7_list = top7.to_dict(orient="records")

        if len(cat_sum) > 7:
            rest_amount = int(cat_sum.iloc[7:].sum())
            top7_list.append({"category": "Остальное", "amount": rest_amount})

        transfers_cash = expenses_df[expenses_df["category"].isin(["Наличные", "Переводы"])]
        transfers_cash_sum = (
            transfers_cash.groupby("category")["amount_rub"]
            .sum()
            .abs()
            .round(0)
            .astype(int)
            .reset_index()
            .rename(columns={"amount_rub": "amount"})
            .to_dict(orient="records")
        )

        # === Поступления ===
        income_df = period[period["amount_rub"] > 0].copy()
        total_income = int(income_df["amount_rub"].sum())

        income_cat = (
            income_df.groupby("category")["amount_rub"]
            .sum()
            .round(0)
            .astype(int)
            .sort_values(ascending=False)
            .reset_index()
            .rename(columns={"amount_rub": "amount"})
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


def get_cards_info(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Считает по картам: последние 4 цифры, расходы и кешбэк (1%)."""
    amount_col = "amount_rub"
    expenses = df[df[amount_col] < 0].copy()
    if expenses.empty or "card_number" not in expenses.columns:
        return []

    grouped = expenses.groupby("card_number")[amount_col].sum().reset_index()

    result = []
    for _, row in grouped.iterrows():
        card_raw = str(row["card_number"]).replace("*", "").strip()
        last_digits = card_raw[-4:] if card_raw else "0000"

        total_spent = round(abs(row[amount_col]), 0)
        cashback = round(total_spent / 100, 2)

        result.append(
            {
                "last_digits": last_digits,
                "total_spent": int(total_spent),
                "cashback": cashback,
            }
        )

    logger.debug("Собрана информация по %s картам.", len(result))
    return result
