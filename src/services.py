import pandas as pd


def search_transactions(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Поиск по подстроке без учёта регистра в любом текстовом поле."""
    if not query:
        return df

    df_filtered = df.copy()
    query_lower = query.lower()
    mask = pd.Series(False, index=df.index)

    for col in df.select_dtypes(include=["object"]):
        mask = mask | df[col].astype(str).str.lower().str.contains(query_lower, na=False)

    return df_filtered[mask]
