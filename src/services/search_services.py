import pandas as pd

from src.logs.log_config import get_logger

logger = get_logger(__name__)


def simple_search(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Поиск без учёта регистра по всем текстовым полям."""
    if not query:
        logger.debug("Пустой запрос поиска.")
        return df

    try:
        logger.debug("Поиск по запросу: %s", query)
        df_str = df.astype(str)
        words = query.lower().split()

        mask_and = pd.Series(True, index=df.index)
        for word in words:
            mask_word = df_str.apply(lambda col: col.str.lower().str.contains(word, regex=False, na=False)).any(axis=1)
            mask_and &= mask_word

        if mask_and.any():
            return df[mask_and]

        mask_or = pd.Series(False, index=df.index)
        for word in words:
            mask_word = df_str.apply(lambda col: col.str.lower().str.contains(word, regex=False, na=False)).any(axis=1)
            mask_or |= mask_word

        return df[mask_or]

    except Exception as e:
        logger.error("Ошибка поиска транзакций: %s", e, exc_info=True)
        return df.head(0)
