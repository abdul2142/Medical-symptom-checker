"""Medical vocabulary and rule data used by core.py.

Educational content only. Every list here would need clinical review before real-world use.
"""

# Canonical symptom -> everyday phrases, grouped by body system.
SYMPTOMS_BY_SYSTEM = {
    "General": {
        "fever": ["fever", "feverish", "high temperature", "have a temperature", "running a temperature",
                  "burning up", "hot to touch", "pyrexia"],
        "chills": ["chills", "shivering", "shivers", "rigors", "feeling cold", "cold sweats"],
        "fatigue": ["fatigue", "tired", "tiredness", "exhausted", "exhaustion", "no energy", "lethargic",
                    "lethargy", "worn out", "drained", "sleepy all the time"],
        "weakness": ["weakness", "feeling weak", "weak", "no strength"],
        "sweating": ["sweating", "sweaty", "sweats", "excessive sweating", "clammy"],
        "night sweats": ["night sweats", "sweating at night", "drenching sweats"],
        "weight change": ["weight loss", "losing weight", "weight gain", "gaining weight", "unexplained weight change"],
        "loss of appetite": ["loss of appetite", "not hungry", "no appetite", "reduced appetite", "off my food", "not eating"],
        "thirst": ["excessive thirst", "very thirsty", "always thirsty", "thirsty"],
        "frequent hunger": ["always hungry", "increased hunger", "constantly hungry"],
        "dehydration signs": ["dry mouth", "dehydrated", "dehydration", "very dark urine", "not peeing much", "dark urine"],
        "swollen glands": ["swollen glands", "swollen lymph nodes", "enlarged lymph nodes", "lumps in neck"],
        "pale skin": ["pale", "pale skin", "pallor", "looking pale"],
        "jaundice": ["jaundice", "yellow skin", "yellow eyes", "yellowing skin", "yellowing of eyes"],
    },
    "Head & nervous system": {
        "headache": ["headache", "head ache", "head pain", "migraine", "pressure in head", "pounding head",
                     "throbbing head", "splitting headache"],
        "dizziness": ["dizziness", "dizzy", "lightheaded", "light headed", "light-headed", "vertigo",
                      "room spinning", "off balance", "unsteady", "feel faint", "feeling faint"],
        "fainting": ["fainting", "fainted", "passed out", "blacked out", "collapsed", "unconscious",
                     "lost consciousness"],
        "confusion": ["confusion", "confused", "disoriented", "disorientated", "not making sense"],
        "seizure": ["seizure", "seizures", "convulsion", "fits", "fitting"],
        "numbness": ["numbness", "numb", "tingling", "pins and needles"],
        "speech difficulty": ["slurred speech", "speech difficulty", "cannot speak", "can't speak",
                              "trouble speaking", "slurring words"],
        "memory problems": ["memory loss", "forgetful", "forgetting things", "poor memory", "memory problems"],
        "tremor": ["tremor", "shaking hands", "trembling", "shaky"],
        "poor concentration": ["poor concentration", "can't concentrate", "brain fog", "difficulty concentrating"],
    },
    "Mental health": {
        "anxiety": ["anxiety", "anxious", "feeling anxious", "panic", "panic attack", "nervous", "on edge",
                    "worrying all the time"],
        "low mood": ["low mood", "feeling down", "depressed", "depression", "hopeless", "sad all the time",
                     "no motivation", "lost interest"],
        "sleep problems": ["insomnia", "cannot sleep", "can't sleep", "trouble sleeping", "sleep problems",
                           "poor sleep", "waking up at night"],
        "stress": ["stress", "stressed", "overwhelmed", "burnt out", "burned out"],
        "hallucinations": ["hallucinations", "hallucinating", "hearing voices", "seeing things"],
    },
    "Eyes": {
        "eye pain": ["eye pain", "sore eyes", "painful eye", "pain in eye"],
        "red eyes": ["red eyes", "red eye", "bloodshot eyes", "pink eye"],
        "itchy eyes": ["itchy eyes", "itchy eye", "watery eyes", "watering eyes"],
        "eye discharge": ["eye discharge", "sticky eyes", "pus from eye", "crusty eyes"],
        "vision problems": ["blurred vision", "blurry vision", "double vision", "vision loss", "loss of vision",
                            "can't see properly", "seeing spots", "flashing lights", "floaters"],
        "light sensitivity": ["sensitivity to light", "light sensitivity", "light hurts my eyes", "photophobia"],
    },
    "Ear, nose, mouth & throat": {
        "ear pain": ["ear pain", "earache", "ear ache", "sore ear", "ear infection"],
        "hearing loss": ["hearing loss", "can't hear", "muffled hearing", "blocked ear", "ears blocked"],
        "tinnitus": ["tinnitus", "ringing in ears", "ringing in my ears", "buzzing in ears"],
        "sore throat": ["sore throat", "throat pain", "scratchy throat", "painful throat"],
        "difficulty swallowing": ["difficulty swallowing", "painful swallowing", "hard to swallow",
                                  "trouble swallowing", "can't swallow"],
        "hoarseness": ["hoarse", "hoarseness", "lost my voice", "loss of voice", "croaky voice"],
        "runny nose": ["runny nose", "running nose", "blocked nose", "stuffy nose", "nasal congestion",
                       "congestion", "congested", "snotty nose", "sniffles"],
        "sneezing": ["sneezing", "sneeze"],
        "facial pain": ["facial pain", "sinus pain", "sinus pressure", "pain in face"],
        "loss of smell or taste": ["loss of smell", "loss of taste", "can't smell", "can't taste",
                                   "lost my sense of smell", "lost my sense of taste"],
        "nosebleed": ["nosebleed", "nose bleed", "bleeding nose"],
        "toothache": ["toothache", "tooth ache", "tooth pain", "dental pain", "gum pain", "sore gums",
                      "bleeding gums", "jaw pain"],
        "mouth pain": ["mouth ulcer", "mouth ulcers", "mouth sores", "canker sore", "cold sore", "sore mouth"],
    },
    "Breathing": {
        "cough": ["cough", "coughing", "dry cough", "wet cough", "chesty cough", "tickly cough", "phlegm",
                  "mucus", "sputum"],
        "breathing difficulty": ["difficulty breathing", "shortness of breath", "short of breath", "out of breath",
                                 "breathless", "breathlessness", "can't breathe", "cannot breathe",
                                 "can't catch my breath", "struggling to breathe", "trouble breathing",
                                 "hard to breathe"],
        "wheezing": ["wheezing", "wheeze", "wheezy", "whistling breathing"],
        "coughing up blood": ["coughing up blood", "blood in phlegm", "blood in sputum", "haemoptysis", "hemoptysis"],
    },
    "Heart & circulation": {
        "chest pain": ["chest pain", "pain in chest", "pressure in chest", "chest pressure", "tightness in chest",
                       "chest tightness", "tight chest", "chest discomfort", "heavy chest"],
        "palpitations": ["palpitations", "racing heart", "heart racing", "heart beating fast", "pounding heart",
                         "heart pounding", "fluttering heart", "skipped beats", "irregular heartbeat"],
        "leg swelling": ["swollen legs", "swollen ankles", "swollen feet", "leg swelling", "ankle swelling",
                         "puffy ankles"],
        "leg pain": ["leg pain", "calf pain", "pain in leg", "pain in calf"],
        "cold extremities": ["cold hands", "cold feet", "cold fingers"],
    },
    "Digestive": {
        "nausea": ["nausea", "nauseous", "nauseated", "feeling sick", "feel sick", "queasy"],
        "vomiting": ["vomiting", "vomit", "vomited", "throwing up", "threw up", "being sick", "puking", "puke"],
        "diarrhea": ["diarrhea", "diarrhoea", "loose motion", "loose stools", "watery stool", "the runs"],
        "constipation": ["constipation", "constipated", "hard stool", "cannot poop", "can't poop", "not pooping"],
        "abdominal pain": ["abdominal pain", "stomach pain", "stomach ache", "stomachache", "belly pain",
                           "tummy ache", "tummy pain", "stomach cramps", "abdominal cramps"],
        "right lower abdominal pain": ["pain in lower right abdomen", "lower right abdominal pain",
                                       "right lower abdominal pain", "pain in right lower abdomen",
                                       "lower right side pain", "pain in my lower right side",
                                       "right lower quadrant pain"],
        "heartburn": ["heartburn", "acid reflux", "reflux", "indigestion", "burning chest after eating",
                      "acid in throat", "sour taste"],
        "bloating": ["bloating", "bloated", "gas", "gassy", "flatulence"],
        "rectal bleeding": ["blood in stool", "bloody stool", "rectal bleeding", "bleeding from bottom",
                            "blood when wiping", "blood in poo"],
        "anal pain": ["piles", "haemorrhoids", "hemorrhoids", "itchy bottom", "sore bottom"],
    },
    "Urinary & reproductive": {
        "urinary pain": ["painful urination", "burning urination", "pain when urinating", "burning when peeing",
                         "stings when i pee", "pain when peeing"],
        "frequent urination": ["frequent urination", "urinating often", "pee often", "peeing a lot",
                               "urgent need to pee", "urinary urgency", "pee all the time", "peeing all the time",
                               "keep needing to pee", "need to pee a lot", "up at night to pee", "weeing a lot"],
        "blood in urine": ["blood in urine", "bloody urine", "blood in my pee", "pink urine"],
        "flank pain": ["flank pain", "kidney pain", "loin pain", "pain in my side", "side pain"],
        "pelvic pain": ["pelvic pain", "lower abdominal pain", "groin pain"],
        "menstrual pain": ["period pain", "menstrual cramps", "painful periods", "period cramps"],
        "abnormal vaginal bleeding": ["vaginal bleeding", "unexpected bleeding", "bleeding between periods",
                                      "spotting", "heavy periods"],
        "missed period": ["missed period", "late period", "no period"],
        "vaginal discharge": ["vaginal discharge", "unusual discharge", "smelly discharge", "vaginal itching", "thrush"],
        "penile discharge": ["penile discharge", "discharge from penis"],
        "testicular pain": ["testicle pain", "testicular pain", "sore testicle", "pain in testicles", "swollen testicle"],
        "breast symptoms": ["breast pain", "sore breasts", "nipple discharge"],
        "erectile difficulty": ["erectile dysfunction", "difficulty maintaining erection"],
    },
    "Muscles, bones & joints": {
        "back pain": ["back pain", "backache", "back ache", "lower back pain", "sore back", "pain in back"],
        "neck pain": ["neck pain", "sore neck", "pain in neck"],
        "stiff neck": ["stiff neck", "neck stiffness", "can't bend my neck"],
        "joint pain": ["joint pain", "joint ache", "painful joints", "sore joints", "knee pain", "hip pain",
                       "shoulder pain", "elbow pain", "wrist pain", "ankle pain", "stiff joints"],
        "muscle pain": ["muscle pain", "muscle ache", "body aches", "body ache", "aching all over",
                        "sore muscles", "myalgia"],
        "muscle cramps": ["muscle cramps", "leg cramps", "cramp in leg"],
        "arm pain": ["arm pain", "pain in arm"],
        "hand pain": ["hand pain", "finger pain"],
        "foot pain": ["foot pain", "heel pain", "toe pain"],
        "injury": ["injury", "injured", "sprain", "sprained", "twisted ankle", "fell over", "had a fall"],
    },
    "Skin": {
        "rash": ["rash", "skin rash", "spots on skin", "red spots"],
        "itching": ["itching", "itchy", "itchy skin", "itch"],
        "skin redness": ["skin redness", "red skin", "redness"],
        "swelling": ["swelling", "swollen", "inflammation", "puffy"],
        "hives": ["hives", "welts", "urticaria"],
        "blisters": ["blister", "blisters"],
        "dry skin": ["dry skin", "flaky skin", "cracked skin", "eczema"],
        "acne": ["acne", "pimples", "breakouts"],
        "bruising": ["bruising", "bruises", "bruise easily"],
        "wound": ["wound", "cut", "open wound", "graze"],
        "burn": ["burn", "burned skin", "burnt skin", "scald"],
        "bite or sting": ["insect bite", "bee sting", "wasp sting", "bitten", "tick bite", "dog bite"],
        "hair loss": ["hair loss", "losing hair", "hair falling out", "bald patches"],
        "bleeding": ["unusual bleeding", "bleeding easily", "bleeding"],
    },
}

# Free-text body part -> symptom when it appears near a pain word ("my left knee hurts").
BODY_PART_PAIN = {
    "head": "headache", "forehead": "headache", "temple": "headache",
    "chest": "chest pain",
    "stomach": "abdominal pain", "tummy": "abdominal pain", "belly": "abdominal pain",
    "abdomen": "abdominal pain", "gut": "abdominal pain",
    "throat": "sore throat",
    "ear": "ear pain",
    "eye": "eye pain",
    "tooth": "toothache", "teeth": "toothache", "gum": "toothache", "jaw": "toothache",
    "back": "back pain", "spine": "back pain",
    "neck": "neck pain",
    "knee": "joint pain", "hip": "joint pain", "shoulder": "joint pain", "elbow": "joint pain",
    "wrist": "joint pain", "ankle": "joint pain", "joint": "joint pain",
    "leg": "leg pain", "calf": "leg pain", "calve": "leg pain", "thigh": "leg pain", "shin": "leg pain",
    "arm": "arm pain",
    "hand": "hand pain", "finger": "hand pain", "thumb": "hand pain",
    "foot": "foot pain", "feet": "foot pain", "heel": "foot pain", "toe": "foot pain",
    "muscle": "muscle pain", "body": "muscle pain",
    "side": "flank pain", "flank": "flank pain", "kidney": "flank pain",
    "pelvis": "pelvic pain", "groin": "pelvic pain", "bladder": "pelvic pain",
    "testicle": "testicular pain", "testis": "testicular pain", "ball": "testicular pain",
    "breast": "breast symptoms", "nipple": "breast symptoms",
    "bottom": "anal pain", "anus": "anal pain", "rectum": "anal pain",
    "mouth": "mouth pain", "tongue": "mouth pain", "lip": "mouth pain",
    "face": "facial pain", "sinus": "facial pain", "cheek": "facial pain",
    # "it burns when I pee"
    "pee": "urinary pain", "peeing": "urinary pain", "wee": "urinary pain", "weeing": "urinary pain",
    "urinate": "urinary pain", "urinating": "urinary pain", "urination": "urinary pain",
}
LEG_PARTS = {"leg", "calf", "calve", "ankle", "foot", "feet", "thigh", "shin", "toe"}
AIRWAY_PARTS = {"lip", "tongue", "throat"}
BLUE_PARTS = {"lip", "face", "finger", "toe", "hand", "foot", "feet"}
ABDOMEN_PARTS = {"stomach", "tummy", "belly", "abdomen", "side", "gut"}
# "my stomach is fine" — a body part mentioned as unaffected is understood, not unknown.
OK_WORDS = {"fine", "ok", "okay", "normal", "alright"}

# Background that changes the picture, picked up from the description.
CONTEXT_TERMS = {
    "Recent long journey": ["long flight", "long-haul flight", "long haul flight", "long journey", "long drive",
                            "long car journey", "long trip"],
    "Recent surgery or immobility": ["recent surgery", "after surgery", "had surgery", "operation", "bed rest",
                                     "bedridden", "immobile", "in a cast"],
    "Recent travel abroad": ["travelled abroad", "traveled abroad", "back from holiday", "returned from travel",
                             "trip abroad"],
}

# Descriptor kind -> words that describe it.
DESCRIPTORS = {
    "pain": {"pain", "painful", "ache", "aches", "aching", "achy", "hurt", "hurts", "hurting", "sore",
             "soreness", "tender", "throbbing", "stabbing", "sharp", "cramp", "cramps", "cramping",
             "burning", "burns", "pounding", "agony", "sting", "stings", "stinging"},
    "blue": {"blue", "grey", "gray"},
    "swell": {"swollen", "swelling", "puffy", "swelled"},
    "itch": {"itchy", "itching", "itches"},
    "red": {"red", "redness", "inflamed"},
    "numb": {"numb", "numbness", "tingling", "tingly"},
    "bleed": {"bleeding", "bleeds", "bled"},
    "stiff": {"stiff", "stiffness"},
    "weak": {"weak", "weakness"},
}

# Phrases that are only red flags (not ordinary symptoms).
RED_FLAG_PHRASES = {
    "RF_ONE_SIDED_WEAKNESS": ["one-sided weakness", "one sided weakness", "face drooping", "drooping face",
                              "weakness on one side", "can't lift my arm", "arm weakness on one side"],
    "RF_SEVERE_BLEEDING": ["heavy bleeding", "uncontrolled bleeding", "bleeding won't stop",
                           "bleeding that won't stop", "vomiting blood", "throwing up blood"],
    "RF_SUDDEN_SEVERE_HEADACHE": ["worst headache", "worst headache of my life", "sudden severe headache",
                                  "thunderclap headache"],
    "RF_SEVERE_ALLERGY": ["swelling of tongue", "swollen tongue", "swollen lips", "lips swelling",
                          "throat closing", "throat swelling", "anaphylaxis", "anaphylactic"],
    "RF_MENINGITIS_SIGNS": ["rash that doesn't fade", "rash does not fade", "non-blanching rash",
                            "rash doesn't fade when pressed"],
    "RF_SELF_HARM": ["suicidal", "suicide", "kill myself", "end my life", "want to die", "self harm",
                     "self-harm", "harm myself"],
    "RF_BLUE_LIPS": ["blue lips", "lips turning blue", "blue skin", "grey lips", "gray lips"],
    "RF_UNRESPONSIVE": ["can't wake", "cannot wake", "unresponsive", "won't wake up", "hard to wake"],
    "RF_SUDDEN_VISION_LOSS": ["sudden vision loss", "sudden loss of vision", "suddenly can't see", "sudden blindness"],
    "RF_SEVERE_ABDOMINAL_PAIN": ["sudden severe abdominal pain", "sudden severe stomach pain", "rigid abdomen",
                                 "rigid stomach"],
    "RF_TESTICULAR_TORSION": ["sudden testicle pain", "sudden testicular pain", "sudden pain in testicle"],
}

# Ordinary symptoms that are emergency warning signs on their own.
SYMPTOM_RED_FLAGS = {
    "chest pain": "RF_CHEST_PAIN",
    "breathing difficulty": "RF_BREATHING_DIFFICULTY",
    "confusion": "RF_CONFUSION",
    "fainting": "RF_FAINTING",
    "speech difficulty": "RF_SPEECH",
    "seizure": "RF_SEIZURE",
}

FLAG_LABELS = {
    "RF_CHEST_PAIN": "Chest pain or pressure",
    "RF_BREATHING_DIFFICULTY": "Difficulty breathing",
    "RF_CONFUSION": "New confusion",
    "RF_FAINTING": "Fainting or collapse",
    "RF_UNRESPONSIVE": "Unresponsive or hard to wake",
    "RF_ONE_SIDED_WEAKNESS": "Face drooping or weakness on one side",
    "RF_SPEECH": "Slurred or lost speech",
    "RF_SEIZURE": "Seizure",
    "RF_SUDDEN_VISION_LOSS": "Sudden loss of vision",
    "RF_SEVERE_BLEEDING": "Heavy bleeding or vomiting blood",
    "RF_SUDDEN_SEVERE_HEADACHE": "Sudden, worst-ever headache",
    "RF_SEVERE_ALLERGY": "Swelling of lips, tongue or throat",
    "RF_BLUE_LIPS": "Blue or grey lips or skin",
    "RF_MENINGITIS_SIGNS": "Fever with stiff neck, light sensitivity or a rash that doesn't fade",
    "RF_SEVERE_ABDOMINAL_PAIN": "Sudden, severe abdominal pain",
    "RF_TESTICULAR_TORSION": "Sudden, severe testicle pain",
    "RF_SELF_HARM": "Thoughts of self-harm or suicide",
}

SERIOUS_CONCERN_PHRASES = [
    "cancer", "tumor", "tumour", "lump in breast", "breast lump", "unexplained lump", "new lump",
    "unexplained weight loss", "black stool", "black poo", "tarry stool", "persistent bleeding",
    "changing mole", "mole that has changed",
]

# Single symptoms that need professional review even when mild.
SYMPTOM_MIN_STATUS = {
    "testicular pain": ("prompt", "Testicle pain should be checked the same day — sudden severe pain is an emergency."),
    "rectal bleeding": ("prompt", "Blood in the stool should be checked by a doctor."),
    "coughing up blood": ("prompt", "Coughing up blood needs same-day medical assessment."),
    "blood in urine": ("prompt", "Blood in urine should always be checked by a doctor."),
    "vision problems": ("prompt", "New changes in vision should be assessed the same day."),
    "jaundice": ("prompt", "Yellowing of the skin or eyes needs prompt medical assessment."),
    "hallucinations": ("prompt", "New hallucinations need prompt medical assessment."),
    "right lower abdominal pain": ("prompt", "Pain in the lower right abdomen can be appendicitis and needs same-day assessment."),
    "difficulty swallowing": ("consider", "Ongoing difficulty swallowing should be reviewed by a doctor."),
    "leg swelling": ("consider", "New leg or ankle swelling should be reviewed by a doctor."),
    "breast symptoms": ("consider", "Breast changes should be checked by a doctor."),
    "hearing loss": ("consider", "Sudden hearing loss should be assessed promptly."),
    "bite or sting": ("consider", "Animal bites and spreading reactions to stings often need treatment."),
}

RISK_FACTORS = [
    "Pregnant",
    "Long-term condition (heart, lung, kidney, diabetes)",
    "Weakened immune system",
    "Takes blood thinners",
]

# Words in the description that imply a risk factor ("I'm diabetic", "on warfarin").
RISK_FACTOR_TERMS = {
    "Pregnant": ["pregnant", "pregnancy", "expecting a baby"],
    "Long-term condition (heart, lung, kidney, diabetes)": [
        "diabetes", "diabetic", "asthma", "asthmatic", "copd", "heart disease", "heart failure",
        "heart condition", "kidney disease", "high blood pressure", "hypertension", "lung disease", "epilepsy"],
    "Weakened immune system": ["chemotherapy", "chemo", "immunosuppressed", "immunocompromised", "hiv",
                               "transplant", "on steroids"],
    "Takes blood thinners": ["blood thinner", "blood thinners", "warfarin", "apixaban", "rivaroxaban",
                             "eliquis", "xarelto", "clopidogrel", "heparin"],
}

SEVERE_WORDS = {"severe", "severely", "unbearable", "excruciating", "agonising", "agonizing", "terrible",
                "extreme", "intense", "worst", "awful", "horrible", "crippling", "agony"}
MODERATE_WORDS = {"moderate", "bad", "significant", "considerable"}
MILD_WORDS = {"mild", "slight", "slightly", "minor"}
WORSENING_PHRASES = ["getting worse", "worsening", "worse and worse", "keeps getting worse", "deteriorating",
                     "spreading"]
SUDDEN_WORDS = {"sudden", "suddenly", "abrupt", "abruptly"}

# Words carrying no clinical meaning; excluded when measuring how much of a description was understood.
STOPWORDS = set("""
i i'm im i've ive i'd me my mine myself we our us you your he she his her him they them their it it's its
this that these those there here a an the and or but so if then than as of in on at to from by with for
about into over under after before since during until up down out off around through again also just only
very really quite too bit little lot lots some any all both each more most other much many such
have has had having am is are was were be been being do does did doing get got getting gets feel feels
feeling felt keep keeps kept started start starting began seem seems think maybe probably now today
yesterday tonight morning night evening afternoon week weeks day days hour hours month months year years
time times ago last past still always sometimes often when while what which who how why where can could
would should will may might must like kind sort thing things something anything nothing everything help
please doctor hi hello thanks thank worried concerned suffering experiencing symptoms symptom problem
problems issue issues no not without never don't dont doesn't didn't haven't hasn't cannot denies denied
left right new old same one two three four five six seven eight nine ten few couple several half
lately recently constant constantly come comes coming goes going went around kinda pretty fairly whole
been having has getting turning turned every need needs needing want wants fine ok okay normal alright
""".split())

# Educational pattern library. These are possible explanations, not diagnoses.
# `requires`: each set must share at least one symptom with the case for the pattern to be considered.
CONDITION_GUIDANCE = {
    "Common cold / viral upper-respiratory infection": {
        "signals": {"runny nose", "sneezing", "cough", "sore throat", "hoarseness"},
        "requires": [{"runny nose", "sneezing", "sore throat"}],
        "care": "Rest, drink fluids, use warm liquids, and consider saline nasal spray. Ask a pharmacist before using medicines, especially for children, pregnancy, or chronic illness.",
        "avoid": "Do not start antibiotics without a clinician's prescription — they do not treat viral colds.",
        "seek_help": ["Symptoms last more than 10 days or improve then worsen", "High fever that will not come down"],
    },
    "Influenza-like illness": {
        "signals": {"fever", "chills", "cough", "muscle pain", "fatigue", "headache", "sore throat"},
        "requires": [{"fever", "chills", "muscle pain"}],
        "care": "Rest, hydrate, and monitor temperature. Antiviral treatment may help high-risk people if started early — contact a clinician promptly if that applies to you.",
        "avoid": "Do not rely on this demo to distinguish influenza, COVID-19, or another infection.",
        "seek_help": ["Breathlessness or chest pain", "Fever lasting more than 3 days"],
    },
    "COVID-19-like illness": {
        "signals": {"fever", "cough", "fatigue", "loss of smell or taste", "sore throat", "headache", "muscle pain"},
        "requires": [{"fever", "cough", "loss of smell or taste"}],
        "care": "Consider a test if available, rest, stay hydrated, and follow local guidance on staying away from others. High-risk people may be eligible for treatment if they act early.",
        "avoid": "Avoid contact with vulnerable people while you have symptoms.",
        "seek_help": ["Breathlessness, especially at rest", "Blue lips or confusion"],
    },
    "Strep-throat / tonsillitis-like illness": {
        "signals": {"sore throat", "fever", "swollen glands", "difficulty swallowing", "headache"},
        "requires": [{"sore throat"}],
        "care": "Rest, drink cool fluids, and use throat lozenges or warm salt-water gargles (adults). A clinician can check whether a throat swab or antibiotics are needed.",
        "avoid": "Do not use leftover antibiotics.",
        "seek_help": ["Difficulty breathing or swallowing saliva", "Unable to open the mouth fully or a muffled voice"],
        "min_status": "consider",
    },
    "Ear-infection-like symptoms": {
        "signals": {"ear pain", "fever", "hearing loss", "tinnitus"},
        "requires": [{"ear pain"}],
        "care": "Most ear infections improve in 3 days. A warm compress may ease discomfort; ask a pharmacist about suitable pain relief.",
        "avoid": "Do not put cotton buds or drops in the ear unless advised.",
        "seek_help": ["Swelling or redness behind the ear", "Discharge from the ear or symptoms over 3 days"],
    },
    "Sinusitis-like symptoms": {
        "signals": {"facial pain", "runny nose", "headache", "fever", "loss of smell or taste"},
        "requires": [{"facial pain", "runny nose"}],
        "care": "Rest, stay hydrated, and try saline nasal rinses or steam. Most cases settle within 2–3 weeks.",
        "avoid": "Antibiotics are rarely needed — take them only if prescribed.",
        "seek_help": ["Swelling or redness around the eyes", "Severe headache or symptoms lasting over 3 weeks"],
    },
    "Asthma / wheeze-like symptoms": {
        "signals": {"wheezing", "breathing difficulty", "cough", "chest pain"},
        "requires": [{"wheezing"}],
        "care": "If you have a prescribed reliever inhaler, use it as directed in your asthma plan. New wheezing needs a clinician's assessment.",
        "avoid": "Avoid smoke and known triggers.",
        "seek_help": ["Reliever not helping or needed more than every 4 hours", "Too breathless to speak in full sentences"],
        "min_status": "prompt",
    },
    "Chest-infection / pneumonia-like illness": {
        "signals": {"cough", "fever", "chills", "breathing difficulty", "chest pain", "fatigue"},
        "requires": [{"cough"}, {"fever", "chills"}],
        "care": "Rest and drink fluids. A clinician should listen to your chest to decide whether antibiotics are needed.",
        "avoid": "Do not ignore breathlessness or chest pain.",
        "seek_help": ["Breathlessness at rest", "Confusion, blue lips or coughing up blood"],
        "min_status": "consider",
    },
    "Gastroenteritis-like illness": {
        "signals": {"diarrhea", "vomiting", "nausea", "abdominal pain", "fever"},
        "requires": [{"diarrhea", "vomiting"}],
        "care": "Take frequent small sips of oral rehydration solution and eat light foods as tolerated. Most cases settle within 2–3 days.",
        "avoid": "Do not give anti-diarrhoeal medicines to young children, or use them when there is blood or fever, without medical advice.",
        "seek_help": ["Blood in vomit or stool", "Unable to keep fluids down for 24 hours", "Very little urine or dizziness on standing"],
    },
    "Appendicitis-like symptoms": {
        "signals": {"right lower abdominal pain", "abdominal pain", "fever", "nausea", "vomiting", "loss of appetite"},
        "requires": [{"right lower abdominal pain"}],
        "care": "Get a same-day medical assessment. Do not eat or drink much until assessed in case surgery is needed.",
        "avoid": "Avoid strong painkillers before assessment if possible, as they can mask worsening pain.",
        "seek_help": ["Pain that suddenly gets much worse or spreads across the abdomen", "High fever or a hard, rigid tummy"],
        "min_status": "prompt",
    },
    "Kidney-stone-like symptoms": {
        "signals": {"flank pain", "blood in urine", "nausea", "vomiting", "urinary pain"},
        "requires": [{"flank pain"}],
        "care": "Drink plenty of water and get a medical assessment for pain relief and imaging.",
        "avoid": "Do not ignore fever with flank pain — that can mean infection.",
        "seek_help": ["Fever or shivering", "Pain not controlled by pain relief or unable to pass urine"],
        "min_status": "prompt",
    },
    "Kidney-infection-like symptoms": {
        "signals": {"flank pain", "fever", "chills", "urinary pain", "frequent urination", "vomiting"},
        "requires": [{"flank pain"}, {"fever", "chills"}],
        "care": "Needs same-day medical assessment and usually antibiotics.",
        "avoid": "Do not wait to see if it settles on its own.",
        "seek_help": ["Confusion, very high fever or vomiting that stops you keeping fluids down"],
        "min_status": "prompt",
    },
    "Urinary-tract-infection-like symptoms": {
        "signals": {"urinary pain", "frequent urination", "pelvic pain", "blood in urine"},
        "requires": [{"urinary pain", "frequent urination"}],
        "care": "Arrange a clinician or pharmacist assessment for urine testing and treatment. Drink normal amounts of water unless a clinician has restricted fluids.",
        "avoid": "Do not self-prescribe antibiotics; fever, flank pain, vomiting, or pregnancy needs prompt assessment.",
        "seek_help": ["Fever, shivering or pain in the side/back", "Vomiting or confusion"],
        "min_status": "consider",
    },
    "Acid-reflux-like symptoms": {
        "signals": {"heartburn", "bloating", "nausea", "abdominal pain"},
        "requires": [{"heartburn"}],
        "care": "Try smaller meals, avoid lying down soon after eating, and identify trigger foods. A pharmacist can advise on antacids.",
        "avoid": "Chest pressure, breathlessness, sweating, or pain spreading to the arm/jaw requires emergency evaluation.",
        "seek_help": ["Difficulty swallowing or unexplained weight loss", "Vomiting blood or black stools"],
    },
    "Irritable-bowel-like symptoms": {
        "signals": {"abdominal pain", "bloating", "diarrhea", "constipation"},
        "requires": [{"abdominal pain", "bloating"}, {"diarrhea", "constipation"}],
        "care": "Keep a food and symptom diary, eat regular meals, and increase soluble fibre gradually. A doctor should confirm the diagnosis.",
        "avoid": "Do not assume ongoing bowel changes are IBS without a medical check, especially over age 50.",
        "seek_help": ["Blood in stool or unexplained weight loss", "Symptoms waking you at night"],
    },
    "Haemorrhoid-like symptoms": {
        "signals": {"anal pain", "rectal bleeding", "itching", "constipation"},
        "requires": [{"anal pain", "rectal bleeding"}],
        "care": "Eat plenty of fibre, drink fluids, and avoid straining. A pharmacist can recommend soothing creams.",
        "avoid": "Do not assume rectal bleeding is piles without a medical check.",
        "seek_help": ["Heavy bleeding or dark/black stool", "Bleeding with weight loss or change in bowel habit"],
    },
    "Tension-headache-like symptoms": {
        "signals": {"headache", "neck pain", "stiff neck", "muscle pain", "fatigue", "stress"},
        "requires": [{"headache"}],
        "care": "Rest in a quiet environment, maintain hydration, take screen breaks, and manage stress.",
        "avoid": "Avoid using pain relievers more than a few days a week, which can cause rebound headaches.",
        "seek_help": ["Sudden worst-ever headache", "Headache with fever and stiff neck", "Weakness, confusion or vision loss"],
    },
    "Migraine-like symptoms": {
        "signals": {"headache", "nausea", "light sensitivity", "vomiting", "vision problems"},
        "requires": [{"headache"}],
        "care": "Rest in a dark, quiet room, stay hydrated, and keep a headache diary to identify triggers. A clinician can advise on treatment.",
        "avoid": "Avoid skipping meals, irregular sleep, and overuse of pain relievers.",
        "seek_help": ["First-ever severe headache, especially over age 50", "Headache with weakness, confusion or speech problems"],
    },
    "Inner-ear / vertigo-like symptoms": {
        "signals": {"dizziness", "nausea", "vomiting", "hearing loss", "tinnitus"},
        "requires": [{"dizziness"}],
        "care": "Sit or lie down when dizzy, get up slowly, and avoid driving. A doctor can check for causes such as inner-ear problems.",
        "avoid": "Avoid heights, ladders and driving while dizzy.",
        "seek_help": ["Dizziness with slurred speech, weakness or double vision", "Sudden hearing loss"],
        "min_status": "consider",
    },
    "Conjunctivitis-like symptoms": {
        "signals": {"red eyes", "itchy eyes", "eye discharge", "eye pain"},
        "requires": [{"red eyes", "eye discharge"}],
        "care": "Clean the eyelids gently with cooled boiled water, avoid rubbing the eyes, and do not share towels.",
        "avoid": "Do not wear contact lenses until symptoms have cleared.",
        "seek_help": ["Changes in vision or sensitivity to light", "Severe eye pain", "Symptoms in a newborn baby"],
    },
    "Hay-fever / allergy-like symptoms": {
        "signals": {"sneezing", "runny nose", "itchy eyes", "itching"},
        "requires": [{"sneezing", "itchy eyes"}],
        "care": "Reduce exposure to triggers, rinse eyes and nose with saline, and ask a pharmacist about antihistamines.",
        "avoid": "Tongue/throat swelling or breathing difficulty requires emergency help, not home treatment.",
        "seek_help": ["Swelling of lips, tongue or throat", "Wheezing or difficulty breathing"],
    },
    "Hives / allergic-skin-reaction-like symptoms": {
        "signals": {"hives", "itching", "rash", "swelling"},
        "requires": [{"hives"}],
        "care": "Avoid the suspected trigger, keep skin cool, and ask a pharmacist about antihistamines.",
        "avoid": "Do not ignore any swelling of the face, lips or tongue.",
        "seek_help": ["Swelling of lips, tongue or throat", "Difficulty breathing or feeling faint"],
    },
    "Skin-irritation / dermatitis-like symptoms": {
        "signals": {"rash", "itching", "skin redness", "dry skin"},
        "requires": [{"rash", "dry skin", "skin redness"}],
        "care": "Use fragrance-free moisturiser, avoid suspected irritants, and keep the area cool. A pharmacist can advise on suitable creams.",
        "avoid": "Avoid scratching and harsh soaps.",
        "seek_help": ["Rash spreading quickly, hot or painful skin, or fever", "A rash that does not fade when pressed"],
    },
    "Cellulitis-like (skin infection) symptoms": {
        "signals": {"skin redness", "swelling", "fever", "wound", "chills"},
        "requires": [{"skin redness"}, {"swelling", "fever"}],
        "care": "Needs a same-day assessment — skin infections usually need antibiotics. Mark the edge of the redness with a pen to track spread.",
        "avoid": "Do not wait if redness is spreading.",
        "seek_help": ["Redness spreading quickly", "Fever, shivering or feeling very unwell"],
        "min_status": "prompt",
    },
    "Shingles-like symptoms": {
        "signals": {"rash", "blisters", "numbness", "fatigue", "fever"},
        "requires": [{"blisters"}],
        "care": "See a pharmacist or doctor within 3 days of the rash appearing — antiviral treatment works best early.",
        "avoid": "Avoid contact with pregnant people, newborns, and people with weak immune systems until blisters crust.",
        "seek_help": ["Rash near the eye or vision changes", "Weakened immune system"],
        "min_status": "consider",
    },
    "Musculoskeletal-strain-like symptoms": {
        "signals": {"back pain", "neck pain", "muscle pain", "joint pain", "injury"},
        "requires": [{"back pain", "neck pain", "muscle pain", "joint pain"}],
        "care": "Keep gently active, use heat or cold packs, and return to normal activities gradually. Most strains improve within a few weeks.",
        "avoid": "Avoid prolonged bed rest and heavy lifting until pain eases.",
        "seek_help": ["Numbness around the genitals or buttocks, or loss of bladder/bowel control", "Pain after a fall or injury, or with fever"],
    },
    "Sciatica-like symptoms": {
        "signals": {"back pain", "leg pain", "numbness", "weakness"},
        "requires": [{"back pain"}, {"leg pain", "numbness"}],
        "care": "Keep moving gently, use heat packs, and try gentle stretches. Most sciatica improves in 4–6 weeks.",
        "avoid": "Avoid sitting for long periods.",
        "seek_help": ["Numbness around the genitals/buttocks or loss of bladder/bowel control (emergency)", "Weakness in both legs"],
        "min_status": "consider",
    },
    "Gout / inflammatory-joint-like symptoms": {
        "signals": {"joint pain", "swelling", "skin redness", "fever"},
        "requires": [{"joint pain"}, {"swelling", "skin redness"}],
        "care": "Rest and raise the joint, apply an ice pack wrapped in a towel, and arrange a medical review.",
        "avoid": "Avoid alcohol and putting weight on the joint.",
        "seek_help": ["Hot swollen joint with fever — this can be a joint infection"],
        "min_status": "consider",
    },
    "Deep-vein-thrombosis-like symptoms": {
        "signals": {"leg pain", "leg swelling", "skin redness"},
        "requires": [{"leg pain"}, {"leg swelling"}],
        "care": "Needs a same-day assessment to rule out a blood clot.",
        "avoid": "Do not massage the leg.",
        "seek_help": ["Sudden breathlessness or chest pain — call emergency services"],
        "min_status": "prompt",
    },
    "Dental-infection-like symptoms": {
        "signals": {"toothache", "swelling", "fever", "facial pain"},
        "requires": [{"toothache"}],
        "care": "See a dentist — tooth pain usually needs dental treatment. Rinse with warm salt water and avoid very hot or cold food.",
        "avoid": "Do not place painkillers directly on the gum.",
        "seek_help": ["Swelling spreading to the eye or neck", "Difficulty swallowing or breathing"],
        "min_status": "consider",
    },
    "Dehydration-like symptoms": {
        "signals": {"thirst", "dehydration signs", "dizziness", "weakness", "fatigue"},
        "requires": [{"thirst", "dehydration signs"}],
        "care": "Sip water or oral rehydration solution and address fluid loss.",
        "avoid": "People with fluid restrictions or serious kidney/heart conditions should follow their clinician's advice.",
        "seek_help": ["Fainting or confusion", "No urine for 8 hours or more"],
    },
    "High-blood-sugar-like symptoms": {
        "signals": {"thirst", "frequent urination", "frequent hunger", "weight change", "fatigue", "vision problems"},
        "requires": [{"thirst", "frequent urination"}],
        "care": "Arrange a blood test with a doctor — these symptoms together can indicate diabetes, which is very treatable once diagnosed.",
        "avoid": "Do not try to self-diagnose or self-treat with diet changes alone before testing.",
        "seek_help": ["Vomiting, abdominal pain, or rapid breathing", "Drowsiness or confusion"],
        "min_status": "consider",
    },
    "Anaemia-like symptoms": {
        "signals": {"fatigue", "pale skin", "breathing difficulty", "dizziness", "palpitations", "weakness"},
        "requires": [{"pale skin", "fatigue"}],
        "care": "A simple blood test can check for anaemia. Arrange a routine appointment.",
        "avoid": "Do not start iron supplements without a test.",
        "seek_help": ["Chest pain or breathlessness at rest", "Black stools or heavy bleeding"],
        "min_status": "consider",
    },
    "Anxiety-like symptoms": {
        "signals": {"anxiety", "palpitations", "sleep problems", "dizziness", "stress", "sweating"},
        "requires": [{"anxiety", "stress"}],
        "care": "Slow breathing exercises, regular sleep, physical activity, and reducing caffeine can help. Talking therapies are effective — a doctor can refer you.",
        "avoid": "Do not assume chest pain or palpitations are anxiety without a medical check.",
        "seek_help": ["Chest pain or fainting", "Thoughts of harming yourself"],
    },
    "Low-mood / depression-like symptoms": {
        "signals": {"low mood", "sleep problems", "fatigue", "loss of appetite", "poor concentration"},
        "requires": [{"low mood"}],
        "care": "Talk to someone you trust and book an appointment with a doctor — depression is common and treatable with talking therapies and/or medicine.",
        "avoid": "Avoid using alcohol or drugs to cope.",
        "seek_help": ["Thoughts of self-harm or suicide — contact a crisis line or emergency services"],
        "min_status": "consider",
    },
    "Menstrual-pain-like symptoms": {
        "signals": {"menstrual pain", "pelvic pain", "abdominal pain", "bloating", "back pain"},
        "requires": [{"menstrual pain"}],
        "care": "Heat packs, gentle exercise and rest can help. A pharmacist can advise on pain relief.",
        "avoid": "Do not ignore periods that are much heavier or more painful than usual.",
        "seek_help": ["Severe pain with fever or fainting", "Possible pregnancy with pain or bleeding"],
    },
    "Genital-infection-like symptoms": {
        "signals": {"vaginal discharge", "penile discharge", "urinary pain", "pelvic pain", "itching"},
        "requires": [{"vaginal discharge", "penile discharge"}],
        "care": "A pharmacist, doctor or sexual-health clinic can test and treat. Many infections are easily treated.",
        "avoid": "Avoid sex until assessed and treated.",
        "seek_help": ["Fever or pelvic pain", "Symptoms during pregnancy"],
        "min_status": "consider",
    },
}
