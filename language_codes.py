"""
LocalLearn AI - Language Codes
--------------------------------
Single source of truth for all supported language codes.

Usage:
    from language_codes import LanguageCode, validate_language, LANGUAGE_NAMES

    lang = LanguageCode.HI          # "hi"
    validate_language("fr")         # raises ValueError
"""

from enum import Enum


# ---------------------------------------------------------------------------
# ENUM
# ---------------------------------------------------------------------------

class LanguageCode(str, Enum):
    """
    Stable language codes used throughout the LocalLearn AI pipeline.

    Inherits from str so that a LanguageCode value can be compared and
    serialised exactly like a plain string:

        LanguageCode.HI == "hi"   # True
        json.dumps({"lang": LanguageCode.HI})  # '{"lang": "hi"}'
    """
    EN = "en"   # English
    HI = "hi"   # Hindi       — हिन्दी
    TA = "ta"   # Tamil       — தமிழ்
    TE = "te"   # Telugu      — తెలుగు
    MR = "mr"   # Marathi     — मराठी


# ---------------------------------------------------------------------------
# HUMAN-READABLE DISPLAY NAMES
# ---------------------------------------------------------------------------

LANGUAGE_NAMES: dict[str, str] = {
    LanguageCode.EN: "English",
    LanguageCode.HI: "Hindi",
    LanguageCode.TA: "Tamil",
    LanguageCode.TE: "Telugu",
    LanguageCode.MR: "Marathi",
}

# Native script names — used in Ollama prompts to help the model
LANGUAGE_NATIVE_NAMES: dict[str, str] = {
    LanguageCode.EN: "English",
    LanguageCode.HI: "हिन्दी (Hindi)",
    LanguageCode.TA: "தமிழ் (Tamil)",
    LanguageCode.TE: "తెలుగు (Telugu)",
    LanguageCode.MR: "मराठी (Marathi)",
}

DEFAULT_LANGUAGE = LanguageCode.EN


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def validate_language(code: str) -> LanguageCode:
    """
    Validate and normalise a language code string.

    Parameters
    ----------
    code : str
        A language code such as "hi", "en", "TA" (case-insensitive).

    Returns
    -------
    LanguageCode
        The corresponding LanguageCode enum member.

    Raises
    ------
    ValueError
        If the code is not one of the supported languages, with a clear
        message listing the valid options.

    Examples
    --------
    >>> validate_language("hi")
    <LanguageCode.HI: 'hi'>
    >>> validate_language("HI")
    <LanguageCode.HI: 'hi'>
    >>> validate_language("fr")
    ValueError: Unsupported language 'fr'. Supported languages: en, hi, ta, te, mr
    """
    normalised = code.strip().lower()
    valid_codes = [lc.value for lc in LanguageCode]

    if normalised not in valid_codes:
        supported = ", ".join(valid_codes)
        raise ValueError(
            f"Unsupported language '{code}'. "
            f"Supported languages: {supported}"
        )

    return LanguageCode(normalised)


def language_display(code: str | LanguageCode) -> str:
    """
    Return the human-readable display name for a language code.

    Parameters
    ----------
    code : str | LanguageCode
        A language code value such as "hi" or LanguageCode.HI.

    Returns
    -------
    str
        Display name, e.g. "Hindi".
    """
    lc = validate_language(str(code)) if not isinstance(code, LanguageCode) else code
    return LANGUAGE_NAMES[lc]
