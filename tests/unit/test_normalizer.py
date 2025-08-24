from yc_matcher.infrastructure.utils.normalize import hash_profile_text, normalize_profile_text


def test_normalizer_collapses_space_case_and_punct():
    a = "John  DOE\nProject: EEG-AI!!!"
    b = "john doe project eeg ai"
    assert normalize_profile_text(a) == b
    assert hash_profile_text(a) == hash_profile_text(b)
