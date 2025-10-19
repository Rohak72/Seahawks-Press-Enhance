import spacy

# Cache the spaCy model to keep it in memory and reduce latency on reaccesses.
NLP_MODEL = None

def _load_spacy_model():
    """
    Loads the spaCy model into a global variable for reuse.
    """

    global NLP_MODEL
    if NLP_MODEL is None:
        print("NER Service: Loading spaCy model for the first time...")
        NLP_MODEL = spacy.load("en_core_web_sm")
        print("NER Service: spaCy model loaded successfully.")

def infer_person_from_title(text: str):
    """
    Uses spaCy's Named Entity Recognition to find the first person's name in a string.
    Returns the name as a string, or None if no person is found.
    """

    _load_spacy_model()

    if not text:
        return None

    # Process the text with the spaCy NER model, loaded above.
    doc = NLP_MODEL(text)

    # Iterate through all the entities the model found.
    for ent in doc.ents:
        # NOTE: the .label_ tells us what kind of entity it is (e.g., PERSON, ORG, GPE).
        if ent.label_ == "PERSON":
            print(f"NER Service: Found PERSON entity: '{ent.text}'")
            return ent.text

    print("NER Service: No PERSON entity found in the text.")
    return None
