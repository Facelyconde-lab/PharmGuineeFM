import unicodedata


def retirer_accents(texte):
    """"paracetamol" tapé sans accent doit trouver "Paracétamol" en base."""
    if not texte:
        return ""
    forme_decomposee = unicodedata.normalize("NFKD", texte)
    sans_accents = "".join(c for c in forme_decomposee if not unicodedata.combining(c))
    return sans_accents.lower()
