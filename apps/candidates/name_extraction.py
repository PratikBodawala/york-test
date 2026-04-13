import re


def infer_candidate_profile_from_resume_text(text: str) -> dict[str, str]:
    lines = [normalize_line(line) for line in text.splitlines()]
    non_empty_lines = [line for line in lines if line]

    candidate_name = extract_candidate_name(non_empty_lines)
    headline = extract_headline(non_empty_lines, candidate_name)

    if candidate_name is None:
        first_name = "Pending"
        last_name = "Candidate"
    else:
        name_parts = candidate_name.split()
        if len(name_parts) == 1:
            first_name = name_parts[0]
            last_name = "Candidate"
        else:
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:])

    return {
        "first_name": first_name,
        "last_name": last_name,
        "headline": headline,
    }


def normalize_line(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_candidate_name(lines: list[str]) -> str | None:
    for line in lines[:8]:
        if looks_like_name(line):
            return " ".join(part.title() for part in line.split())
    return None


def extract_headline(lines: list[str], candidate_name: str | None) -> str:
    for line in lines[:12]:
        if not line:
            continue
        if candidate_name is not None and normalize_line(line).lower() == candidate_name.lower():
            continue
        if "@" in line:
            continue
        if re.search(r"\d{3}", line):
            continue
        if len(line.split()) > 12:
            continue
        return line
    return ""


def looks_like_name(value: str) -> bool:
    if "@" in value:
        return False
    if any(character.isdigit() for character in value):
        return False

    words = value.split()
    if len(words) < 2 or len(words) > 4:
        return False

    allowed_connectors = {"de", "da", "del", "van", "von", "bin"}
    for word in words:
        cleaned_word = word.strip(".,")
        if len(cleaned_word) < 2:
            return False
        if cleaned_word.lower() in allowed_connectors:
            continue
        if not cleaned_word.replace("-", "").replace("'", "").isalpha():
            return False
        if not cleaned_word[0].isalpha():
            return False

    return True
