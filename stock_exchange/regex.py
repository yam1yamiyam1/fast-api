import re


def path_to_regex(pattern: str) -> re.Pattern:
    mod_str = re.sub(r"\{([^}]+)\}", r"(?P<\g<1>>[^/]+)", pattern)
    return re.compile(f"^{mod_str}$")
