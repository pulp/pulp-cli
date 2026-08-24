from pulp_glue.common.context import PreprocessedEntityDefinition, PulpContext, PulpEntityContext


def test_preprocess_entity_is_only_called_once(mock_pulp_ctx: PulpContext) -> None:
    entity_ctx = PulpEntityContext(mock_pulp_ctx)

    preprocessed = entity_ctx._preprocess_entity({})
    assert isinstance(preprocessed, PreprocessedEntityDefinition)

    # Now call it again and see if the returned object is the same, not just equal.
    assert preprocessed is entity_ctx._preprocess_entity(preprocessed)
