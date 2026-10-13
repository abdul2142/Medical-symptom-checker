from api_clients import parse_medlineplus_xml
from core import DISCLAIMER, STATUS_ORDER, analyze_symptoms, build_report, detect_red_flags, normalize_symptoms

STATUS_RANK = {s: i for i, s in enumerate(STATUS_ORDER)}


def test_expanded_vocabulary():
    result = normalize_symptoms("I have dizziness, stomach pain, rash and painful urination")
    assert "dizziness" in result["matched_symptoms"]
    assert "abdominal pain" in result["matched_symptoms"]
    assert "rash" in result["matched_symptoms"]
    assert "urinary pain" in result["matched_symptoms"]


def test_emergency_flags():
    flags = detect_red_flags("I have chest pain and difficulty breathing")
    assert "RF_CHEST_PAIN" in flags
    assert "RF_BREATHING_DIFFICULTY" in flags


def test_red_flags_match_whole_words_only():
    # "fits" (seizure) must not fire on "benefits" or "outfits".
    assert detect_red_flags("mild headache, worried about the benefits of rest") == []


def test_red_flag_routes_to_emergency():
    result = analyze_symptoms("sudden chest pain", "Adult", "Today", "Mild")
    assert result["doctor_status"] == "urgent"
    assert "emergency" in result["care_guidance"].lower()


def test_severe_result_recommends_professional():
    result = analyze_symptoms("fever and body aches", "Adult", "Today", "Severe")
    assert result["doctor_status"] == "prompt"
    assert "professional" in result["reason"].lower()


def test_serious_concern_never_low():
    result = analyze_symptoms("I found an unexplained lump", "Adult", "Today", "Mild")
    assert result["doctor_status"] == "prompt"


def test_persistent_symptoms_recommend_consultation():
    result = analyze_symptoms("cough", "Adult", "More than 1 week", "Mild")
    assert result["doctor_status"] == "prompt"


def test_mild_unrecognised_input_is_low_confidence():
    result = analyze_symptoms("something feels off", "Adult", "Today", "Mild")
    assert result["doctor_status"] == "monitor"
    assert result["overall_confidence"] == 20


def test_pattern_match_suggests_condition():
    result = analyze_symptoms("diarrhea, vomiting and nausea", "Adult", "Today", "Mild")
    assert result["possible_conditions"][0]["name"].startswith("Gastroenteritis")


def test_negated_symptoms_are_not_counted():
    result = analyze_symptoms("I don't have a fever, just a cough", "Adult", "Today", "Mild")
    assert result["matched_symptoms"] == ["cough"]
    assert "Fever" in result["pertinent_negatives"]


def test_negation_is_limited_to_its_clause():
    result = analyze_symptoms("no chest pain but shortness of breath", "Adult", "Today", "Mild")
    assert result["red_flags_triggered"] == ["RF_BREATHING_DIFFICULTY"]
    assert result["doctor_status"] == "urgent"


def test_no_improvement_is_not_a_negation():
    assert normalize_symptoms("no improvement in my cough")["matched_symptoms"] == ["cough"]


def test_typos_and_plurals_are_recognised():
    matched = normalize_symptoms("headaches and diarhea")["matched_symptoms"]
    assert {"headache", "diarrhea"} <= set(matched)


def test_similar_words_do_not_trigger_red_flags():
    assert detect_red_flags("I was painting the fence") == []


def test_fever_with_stiff_neck_is_emergency():
    result = analyze_symptoms("fever and stiff neck", "Adult", "Today", "Mild")
    assert "RF_MENINGITIS_SIGNS" in result["red_flags_triggered"]


def test_checklist_warning_sign_overrides():
    result = analyze_symptoms("sore throat", "Adult", "Today", "Mild", warning_signs=["RF_SEVERE_ALLERGY"])
    assert result["doctor_status"] == "urgent"


def test_infant_fever_needs_same_day_care():
    result = analyze_symptoms("fever", "Infant (under 1)", "Today", "Mild")
    assert result["doctor_status"] == "prompt"
    assert result["contributing_factors"]


def test_pregnancy_with_abdominal_pain_escalates():
    result = analyze_symptoms("stomach pain", "Adult", "Today", "Mild", risk_factors=["Pregnant"])
    assert result["doctor_status"] == "prompt"


def test_self_harm_gives_crisis_guidance():
    result = analyze_symptoms("I feel suicidal", "Adult", "Today", "Mild")
    assert result["doctor_status"] == "urgent"
    assert "crisis" in result["care_setting"].lower()


def test_ordinary_injury_is_not_self_harm():
    assert "RF_SELF_HARM" not in detect_red_flags("I hurt myself falling off a ladder")


def test_patterns_needing_tests_are_not_self_care():
    result = analyze_symptoms("excessive thirst, peeing a lot and very tired", "Adult", "Today", "Mild")
    assert result["doctor_status"] == "consider"


def test_mild_result_has_safety_net():
    result = analyze_symptoms("runny nose and sneezing", "Adult", "Today", "Mild")
    assert result["doctor_status"] == "monitor"
    assert result["safety_net"]


N = "Not specified"


def test_body_part_phrases_are_understood():
    result = analyze_symptoms("My left knee hurts and my ankles are swollen", N, N, "Mild")
    assert set(result["matched_symptoms"]) == {"joint pain", "leg swelling"}
    assert result["understanding"] == 100


def test_body_part_chest_pain_is_emergency():
    assert analyze_symptoms("my chest hurts", N, N, "Mild")["doctor_status"] == "urgent"


def test_fuzzy_match_does_not_bridge_filler_words():
    # "swollen and" once scored 92% against "swollen gland".
    matched = normalize_symptoms("my foot is red and swollen and sore")["matched_symptoms"]
    assert "swollen glands" not in matched


def test_feeling_faint_is_not_fainting():
    result = analyze_symptoms("I feel faint", N, N, "Mild")
    assert "RF_FAINTING" not in result["red_flags_triggered"]
    assert "dizziness" in result["matched_symptoms"]


def test_details_are_extracted_from_text():
    result = analyze_symptoms("my 2 year old has a fever of 39.5C for 3 days, pain is 8/10", N, N, "Mild")
    assert result["age_group"] == "Child"
    assert result["duration"] == "1–3 days"
    assert result["temperature_c"] == 39.5
    assert result["severity"] == "Severe"


def test_fahrenheit_temperature_implies_fever():
    result = analyze_symptoms("sore throat, temp 101F", N, N, "Mild")
    assert "fever" in result["matched_symptoms"]
    assert result["temperature_c"] == 38.3


def test_normal_temperature_is_a_pertinent_negative():
    result = analyze_symptoms("temperature is 36.8, mild cough", N, N, "Mild")
    assert "fever" not in result["matched_symptoms"]
    assert any("36.8" in n for n in result["pertinent_negatives"])


def test_age_number_is_not_a_temperature_or_duration():
    result = analyze_symptoms("I'm 38 years old with a cough", N, N, "Mild")
    assert result["temperature_c"] is None
    assert result["duration"] == N
    assert result["age_group"] == "Adult"


def test_duration_number_is_not_an_age():
    assert analyze_symptoms("I am 5 days into this cough", N, N, "Mild")["age_group"] == N


def test_risk_factors_are_extracted_from_text():
    result = analyze_symptoms("I'm diabetic and on warfarin, I have a nosebleed", N, N, "Mild")
    assert "Takes blood thinners" in result["risk_factors"]
    assert result["doctor_status"] == "prompt"


def test_right_lower_abdominal_pain_suggests_appendicitis():
    result = analyze_symptoms("sharp pain in my lower right abdomen, no appetite, temp 38.2", N, N, "Mild")
    assert result["possible_conditions"][0]["name"].startswith("Appendicitis")
    assert result["doctor_status"] == "prompt"


def test_long_flight_with_swollen_calf_escalates():
    result = analyze_symptoms("calf pain and swollen leg after a long flight", N, N, "Mild")
    assert "Recent long journey" in result["details_from_text"]
    assert result["doctor_status"] == "prompt"


def test_blue_lips_are_an_emergency():
    result = analyze_symptoms("my lips are turning blue", N, N, "Mild")
    assert "RF_BLUE_LIPS" in result["red_flags_triggered"]


def test_facial_swelling_with_toothache_is_dental_not_anaphylaxis():
    result = analyze_symptoms("toothache and my face is swollen", N, N, "Mild")
    assert "RF_SEVERE_ALLERGY" not in result["red_flags_triggered"]
    assert result["possible_conditions"][0]["name"].startswith("Dental")


def test_worsening_raises_level():
    stable = analyze_symptoms("mild cough", N, N, "Mild")
    worse = analyze_symptoms("mild cough that is getting worse", N, N, "Mild")
    assert STATUS_RANK[worse["doctor_status"]] > STATUS_RANK[stable["doctor_status"]]


def test_pattern_requires_its_key_symptom():
    # Headache + nausea must not be called gastroenteritis.
    names = [c["name"] for c in analyze_symptoms("headache and nausea", N, N, "Mild")["possible_conditions"]]
    assert not any(n.startswith("Gastroenteritis") for n in names)
    assert names[0].startswith("Migraine")


def test_understanding_reports_unknown_words():
    result = analyze_symptoms("cough and xyzzy", N, N, "Mild")
    assert "xyzzy" in result["unrecognised_words"]
    assert result["understanding"] < 100


def test_well_described_case_has_high_confidence():
    result = analyze_symptoms("I'm 30, sore throat and fever of 38.5 for 2 days", N, N, "Mild")
    assert result["overall_confidence"] >= 95
    assert result["completeness"] == 100


def test_report_contains_key_fields():
    result = analyze_symptoms("fever and cough", "Adult", "Today", "Mild")
    report = build_report("fever and cough", result, "01 Jan 2026, 09:00")
    assert "fever and cough" in report
    assert result["level_label"] in report
    assert result["care_setting"] in report
    assert "RED-FLAG SCREEN" in report
    assert DISCLAIMER in report


def test_parse_medlineplus_xml():
    xml = """<nlmSearchResult><list>
      <document rank="0" url="https://medlineplus.gov/painrelievers.html">
        <content name="title">&lt;span class="qt0"&gt;Pain&lt;/span&gt; Relievers</content>
        <content name="FullSummary">What are pain relievers?&lt;p&gt;Medicines that reduce pain.&lt;/p&gt;</content>
      </document></list></nlmSearchResult>"""
    [item] = parse_medlineplus_xml(xml)
    assert item["title"] == "Pain Relievers"
    assert item["url"] == "https://medlineplus.gov/painrelievers.html"
    assert item["summary"] == "What are pain relievers? Medicines that reduce pain."
