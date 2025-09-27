from src.app_context import app_context


def t(key: str, default: str | None = None, **kwargs: object) -> str:
    if app_context.i18n_manager:
        return app_context.i18n_manager.i18n(key, default, **kwargs)
    # 如果没有i18n管理器，直接返回默认值或键，并进行格式化
    result = default or key
    if kwargs:
        try:
            return result.format(**kwargs)
        except Exception:
            return result
    return result
