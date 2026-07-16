import re
import time
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from flask import Request

from src.api.api_currency import get_currency_rates
from src.api.api_stocks import get_stock_prices
from src.constants import MESSAGES
from src.logs.log_config import DATA_FILE, get_logger
from src.reports.expenses_reports import (
    expenses_by_category,
    expenses_by_weekday,
    expenses_work_vs_weekend,
)
from src.services.search_services import (
    search_phone_numbers,
    search_transfers,
    simple_search,
)
from src.utils.data_loader import load_transaction
from src.utils.filters_utils import filter_last_3_months
from src.utils.format_utils import format_rub, format_rub_rounded
from src.views import get_cards_info

logger = get_logger(__name__)

_DF: Optional[pd.DataFrame] = None
_CACHE: Dict[str, Dict[str, Any]] = {
    "cur": {"d": None, "t": 0},
    "stock": {"d": None, "t": 0},
}


def get_initial_dataframe() -> pd.DataFrame:
    """Грузит Excel 1 раз."""
    global _DF
    if _DF is None:
        _DF = load_transaction(DATA_FILE)
    return _DF


def cached_currency() -> List[Dict[str, Any]]:
    """Кэш валют 1 час."""
    if _CACHE["cur"]["d"] is None or time.time() - _CACHE["cur"]["t"] > 3600:
        try:
            data = get_currency_rates()
            for c in data:
                c["rate"] = format_rub(c["rate"])
            _CACHE["cur"]["d"] = data
        except Exception:
            _CACHE["cur"]["d"] = []
        _CACHE["cur"]["t"] = time.time()
    result: List[Dict[str, Any]] = _CACHE["cur"]["d"]
    return result


def cached_stocks() -> List[Dict[str, Any]]:
    """Кэш акций 1 час."""
    if _CACHE["stock"]["d"] is None or time.time() - _CACHE["stock"]["t"] > 3600:
        try:
            data = get_stock_prices()
            for s in data:
                s["price"] = format_rub(s["price"])
            _CACHE["stock"]["d"] = data
        except Exception:
            _CACHE["stock"]["d"] = []
        _CACHE["stock"]["t"] = time.time()
    result: List[Dict[str, Any]] = _CACHE["stock"]["d"]
    return result


def _to_records(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], int, int]:
    """df -> (records, count, sum) с целыми суммами и датами."""
    if df is None or df.empty:
        return [], 0, 0
    dc = df.copy()
    dc["date_operation"] = pd.to_datetime(dc["date_operation"]).dt.strftime("%d.%m.%Y")
    dc["amount_rub"] = dc["amount_rub"].abs().round(0).astype(int)
    records: List[Dict[str, Any]] = [{str(k): v for k, v in r.items()} for r in dc.to_dict(orient="records")]
    return records, len(df), int(abs(df["amount_rub"].sum()))


def _fmt_int(x: Any) -> str:
    """Форматирует целую сумму: X XXX XXX."""
    if x is None or pd.isna(x):
        return "0"
    return f"{int(round(float(x))):,}".replace(",", " ")


def _phone_core(q: str) -> Optional[str]:
    """Валидация телефона: 10 цифр или 11 с 7/8."""
    d = re.sub(r"\D", "", q)
    if len(d) == 10:
        return d
    if len(d) == 11 and d[0] in "78":
        return d[1:]
    return None


def _top7(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Топ-7 категорий + Остальное."""
    if df.empty:
        return []
    s = df[df["amount_rub"] < 0].groupby("category")["amount_rub"].sum().abs().sort_values(ascending=False)
    top = s.head(7)
    rest = s.iloc[7:].sum() if len(s) > 7 else 0
    r = [{"category": c, "amount": format_rub_rounded(v)} for c, v in top.items()]
    if rest > 0:
        r.append({"category": "Остальное", "amount": format_rub_rounded(rest)})
    return r


def _top5(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Топ-5 расходов."""
    if df.empty:
        return []
    e = df[df["amount_rub"] < 0].sort_values("amount_rub").head(5)
    return [
        {"date": d.strftime("%d.%m.%Y"), "amount": format_rub_rounded(abs(a)), "category": c}
        for d, a, c in zip(e["date_operation"], e["amount_rub"], e["category"])
    ]


def _top_cash(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Топ-3 категорий по кешбэку."""
    if df.empty or "cashback" not in df.columns:
        return []
    s = df.groupby("category")["cashback"].sum()
    s = s[s > 0].sort_values(ascending=False).head(3)
    return [{"category": c, "cashback": format_rub_rounded(v)} for c, v in s.items()]


def _proc(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Форматирует все числовые колонки отчёта через _fmt_int."""
    if df.empty:
        return []
    dc = df.copy()
    for col in dc.select_dtypes(include="number").columns:
        dc[col] = dc[col].abs().map(_fmt_int)
    records: List[Dict[str, Any]] = [{str(k): v for k, v in r.items()} for r in dc.to_dict(orient="records")]
    return records


def build_dashboard_context(df: pd.DataFrame, request: Request) -> Dict[str, Any]:
    """Собирает весь контекст для index.html."""
    custom_end = request.values.get("custom_end", "").strip()
    ce = pd.to_datetime(custom_end, dayfirst=True, errors="coerce") if custom_end else pd.NaT
    df_rep = filter_last_3_months(df, end_date=ce) if pd.notna(ce) else filter_last_3_months(df)

    ps = pe = ""
    no_data = ""
    if df_rep.empty:
        no_data = MESSAGES["NO_PERIOD"]
    else:
        ps = df_rep["date_operation"].min().strftime("%d.%m.%Y")
        pe = df_rep["date_operation"].max().strftime("%d.%m.%Y")

    s_list: List[Dict[str, Any]] = []
    s_cnt = s_sum = 0
    s_empty = ""
    p_list: List[Dict[str, Any]] = []
    p_cnt = p_sum = 0
    p_err = p_empty = ""
    f_list: List[Dict[str, Any]] = []
    f_cnt = f_sum = 0
    f_empty = ""

    if request.method == "POST":
        f = request.form
        if f.get("search_query", "").strip():
            r = simple_search(df, f.get("search_query", "").strip())
            if r.empty:
                s_empty = MESSAGES["NOT_FOUND"]
            else:
                s_list, s_cnt, s_sum = _to_records(r)
        if "phone_all" in f:
            r = search_phone_numbers(df)
            p_list, p_cnt, p_sum = _to_records(r) if not r.empty else ([], 0, 0)
            if r.empty:
                p_empty = MESSAGES["NO_DATA"]
        if f.get("phone_query", "").strip():
            q = f.get("phone_query", "").strip()
            core = _phone_core(q)
            if not core:
                p_err = MESSAGES["PHONE_INVALID"]
                p_list, p_cnt, p_sum, p_empty = [], 0, 0, ""
            else:
                dd = df["description"].astype(str).apply(lambda x: re.sub(r"\D", "", x))
                r = df[dd.str.contains(core, na=False)]
                if r.empty:
                    p_empty = MESSAGES["NO_DATA"]
                else:
                    p_list, p_cnt, p_sum = _to_records(r)
        if "fl_all" in f:
            r = search_transfers(df)
            f_list, f_cnt, f_sum = _to_records(r) if not r.empty else ([], 0, 0)
            if r.empty:
                f_empty = MESSAGES["NO_DATA"]
        if f.get("fl_query", "").strip():
            base = search_transfers(df)
            r = base[base["description"].astype(str).str.contains(f.get("fl_query", "").strip(), case=False, na=False)]
            if r.empty:
                f_empty = MESSAGES["NOT_FOUND"]
            else:
                f_list, f_cnt, f_sum = _to_records(r)

    df_no = df_rep[~df_rep["category"].str.contains("Перевод", case=False, na=False)] if not df_rep.empty else df_rep
    cards = get_cards_info(df_rep)
    inc = (
        df_rep[df_rep["amount_rub"] > 0].groupby("card_number")["amount_rub"].sum().reset_index()
        if not df_rep.empty
        else pd.DataFrame()
    )
    inc_d: Dict[str, float] = {}
    if not inc.empty:
        inc["last_digits"] = inc["card_number"].astype(str).str.replace("*", "").str[-4:]
        inc_d = dict(zip(inc["last_digits"], inc["amount_rub"]))
    for c in cards:
        c["total_income"] = format_rub_rounded(abs(inc_d.get(c["last_digits"], 0)))
        c["total_spent"] = format_rub_rounded(abs(c["total_spent"]))
        c["cashback"] = format_rub_rounded(abs(c["cashback"]))

    return dict(
        period_start=ps,
        period_end=pe,
        custom_end=custom_end,
        no_data=no_data,
        s_res=s_list,
        s_cnt=s_cnt,
        s_sum=s_sum,
        s_empty=s_empty,
        p_res=p_list,
        p_cnt=p_cnt,
        p_sum=p_sum,
        p_err=p_err,
        p_empty=p_empty,
        f_res=f_list,
        f_cnt=f_cnt,
        f_sum=f_sum,
        f_empty=f_empty,
        top7_with=_top7(df_rep),
        top7_without=_top7(df_no),
        top5_with=_top5(df_rep),
        top5_without=_top5(df_no),
        top3_with=_top_cash(df_rep),
        top3_without=_top_cash(df_no),
        cat_rep=_proc(expenses_by_category(df_rep)),
        wd_with=_proc(expenses_by_weekday(df_rep)),
        wd_without=_proc(expenses_by_weekday(df_no)),
        ww_with=_proc(expenses_work_vs_weekend(df_rep)),
        ww_without=_proc(expenses_work_vs_weekend(df_no)),
        cards=cards,
    )
