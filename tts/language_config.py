"""
LocalLearn AI - Language Voice Configurations
-----------------------------------------------
Per-language voice style descriptions for Indic-Parler TTS.
Consistent voice per language across all beats in a video.
"""

# Voice/style descriptions for each supported language.
# These are passed to the Indic-Parler TTS model as speaker descriptions.
LANGUAGE_VOICE_CONFIGS = {
    "en": {
        "description": (
            "A male speaker speaks clearly in an Indian English accent "
            "at a moderate speed with a calm educational tone. "
            "The recording is very clear with no background noise."
        ),
        "language_name": "English",
    },
    "hi": {
        "description": (
            "एक पुरुष वक्ता स्पष्ट हिंदी उच्चारण के साथ मध्यम गति से शैक्षिक स्वर में बोलता है। "
            "रिकॉर्डिंग बहुत साफ है और कोई पृष्ठभूमि शोर नहीं है।"
        ),
        "language_name": "Hindi",
    },
    "ta": {
        "description": (
            "ஒரு ஆண் பேச்சாளர் தெளிவான தமிழ் உச்சரிப்புடன் மிதமான வேகத்தில் "
            "கல்வி தொனியில் பேசுகிறார். பதிவு மிகவும் தெளிவாக உள்ளது மற்றும் "
            "பின்னணி சத்தம் இல்லை."
        ),
        "language_name": "Tamil",
    },
    "te": {
        "description": (
            "ఒక పురుషుడు స్పష్టమైన తెలుగు ఉచ్ఛారణతో మధ్యస్థ వేగంతో విద్యాపరమైన "
            "స్వరంతో మాట్లాడుతున్నాడు. రికార్డింగ్ చాలా స్పష్టంగా ఉంది మరియు "
            "నేపథ్య శబ్దం లేదు."
        ),
        "language_name": "Telugu",
    },
    "mr": {
        "description": (
            "एक पुरुष स्पष्ट मराठी उच्चारणासह मध्यम गतीने शैक्षणिक स्वरात बोलतो। "
            "रेकॉर्डिंग अतिशय स्पष्ट आहे आणि पार्श्वभूमी आवाज नाही."
        ),
        "language_name": "Marathi",
    },
}


def get_voice_config(language_code: str) -> dict:
    """
    Return the voice configuration for a language code.
    
    Falls back to English if the language is not found.
    """
    return LANGUAGE_VOICE_CONFIGS.get(language_code, LANGUAGE_VOICE_CONFIGS["en"])
