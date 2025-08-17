import pytest

from pulp_cli.generic import prn_regex


@pytest.mark.parametrize(
    "prn,app,model,pk",
    [
        pytest.param(
            "prn:file.fileremote:0198b567-c482-7b28-8628-ea7f4be6d008",
            "file",
            "fileremote",
            "0198b567-c482-7b28-8628-ea7f4be6d008",
            id="good-prn-recognized",
        ),
        pytest.param(
            "prn:a.b:00000000-0000-0000-0000-000000000000",
            "a",
            "b",
            "00000000-0000-0000-0000-000000000000",
            id="single-letter-names-recognized",
        ),
        pytest.param(
            "prn:f1le.f1lerem0te:0198b567-c482-7b28-8628-ea7f4be6d008",
            "f1le",
            "f1lerem0te",
            "0198b567-c482-7b28-8628-ea7f4be6d008",
            id="app-and-model-with-digits",
        ),
    ],
)
def test_prn_match_succeeds_for(prn: str, app: str, model: str, pk: str) -> None:
    match = prn_regex.match(prn)
    assert match
    assert 3 == len(match.groups())
    assert match.group("app") == app
    assert match.group("model") == model
    assert match.group("pk") == pk


@pytest.mark.parametrize(
    "prn",
    [
        pytest.param("", id="empty-str"),
        pytest.param(
            "file.fileremote:0198b567-c482-7b28-8628-ea7f4be6d008", id="doesnt-start-with-prn"
        ),
        pytest.param("prn:filefileremote0198b567-c482-7b28-8628-ea7f4be6d008", id="no-punctuation"),
        pytest.param(
            "prn:file+fileremote:0198b567-c482-7b28-8628-ea7f4be6d00", id="incorrect-punctuation"
        ),
        pytest.param("prn:.fileremote:0198b567-c482-7b28-8628-ea7f4be6d00", id="no-app"),
        pytest.param("prn:file.:0198b567-c482-7b28-8628-ea7f4be6d00", id="no-model"),
        pytest.param("prn:file.fileremote:", id="no-pk"),
        pytest.param("prn:file.fileremote:foo", id="not-pk-shaped"),
        pytest.param("prn:file.fileremote:0198b567c4827b288628ea7f4be6d00", id="no-punc-pk"),
        pytest.param("prn:file.fileremote:0198b567-xxxx-7b28-8628-ea7f4be6d00", id="non-hex-in-pk"),
        pytest.param("prn:file.fileremote:08-04-04-04-12", id="not-a-pk"),
    ],
)
def test_prn_match_fails_for(prn: str) -> None:
    match = prn_regex.match(prn)
    assert not match
