import unicodedata


def retirer_accents(texte):
    """
    Retire les accents d'un texte et le met en minuscule, pour comparer
    "paracetamol" (tapé sans accent par un patient pressé) et "Paracétamol"
    (enregistré avec accent dans la base) comme équivalents.

    Exemple : retirer_accents("Paracétamol") -> "paracetamol"
    """
    if not texte:
        return ""
    forme_decomposee = unicodedata.normalize("NFKD", texte)
    sans_accents = "".join(c for c in forme_decomposee if not unicodedata.combining(c))
    return sans_accents.lower()
