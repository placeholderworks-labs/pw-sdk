import re
from pathlib import Path

TEMPLATE = Path(__file__).parent / "template"
SLUG = re.compile(r"^[a-z][a-z0-9_]{1,40}$")


def names(slug: str) -> dict[str, str]:
    if not SLUG.match(slug):
        raise ValueError("client slug must be lowercase letters, digits and underscores, e.g. acme_travel")
    return {
        "{{slug}}": slug,
        "{{SLUG}}": slug.upper(),
        "{{repo}}": slug.replace("_", "-") + "-adapter",
        "{{Class}}": "".join(part.capitalize() for part in slug.split("_")),
        "{{title}}": " ".join(part.capitalize() for part in slug.split("_")),
    }


def render(text: str, mapping: dict[str, str]) -> str:
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


def scaffold(slug: str, parent: Path) -> Path:
    mapping = names(slug)
    target = parent / mapping["{{repo}}"]
    if target.exists():
        raise FileExistsError(f"{target} already exists")
    for source in TEMPLATE.rglob("*.tmpl"):
        relative = render(str(source.relative_to(TEMPLATE)).removesuffix(".tmpl"), mapping)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(render(source.read_text(), mapping))
    return target
