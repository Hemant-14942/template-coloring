from app.services.template_store import TemplateStore, get_template_store


def template_store() -> TemplateStore:
    return get_template_store()
