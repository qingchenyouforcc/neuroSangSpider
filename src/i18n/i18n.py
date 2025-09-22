from src.app_context import app_context

def t(key: str, default: str = None) -> str:
    if app_context.i18n_manager:
        return app_context.i18n_manager.i18n(key, default)
    return default or key