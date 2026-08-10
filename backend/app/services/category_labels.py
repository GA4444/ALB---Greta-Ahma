"""Human-readable Albanian labels for exercise categories."""

CATEGORY_LABELS_SQ = {
    "listen_write": "Dëgjim dhe shkrim",
    "word_from_description": "Fjala nga përshkrimi",
    "synonyms_antonyms": "Sinonime dhe antonime",
    "albanian_or_loanword": "Fjalë shqipe ose fjalë e huazuar",
    "missing_letter": "Shkronja që mungon",
    "wrong_letter": "Shkronja e gabuar",
    "build_word": "Ndërtimi i fjalës",
    "number_to_word": "Numrat me fjalë",
    "phrases": "Shprehje frazeologjike",
    "spelling_punctuation": "Drejtshkrim dhe pikësim",
    "abstract_concrete": "Fjalë abstrakte dhe konkrete",
    "build_sentence": "Ndërtimi i fjalisë",
    "vocabulary": "Fjalor",
    "spelling": "Drejtshkrim",
    "grammar": "Gramatikë",
    "numbers": "Numrat",
    "punctuation": "Pikësim",
    # Compatibility with categories from older imported data.
    "write": "Shkrim",
    "writing": "Shkrim",
    "read": "Lexim",
    "reading": "Lexim",
    "listen": "Dëgjim",
    "listening": "Dëgjim",
}


def category_label_sq(category: str) -> str:
    normalized = category.strip().lower()
    return CATEGORY_LABELS_SQ.get(
        normalized,
        normalized.replace("_", " ").capitalize(),
    )
