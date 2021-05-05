from esok.util import clean_index

DELETED_SETTINGS_KEYS = [u'version', u'creation_date', u'uuid', u'provided_name']


def test_clean_index():
    index_settings = _create_index_setting()

    okay_setting_key = u'okay_setting'
    okay_setting_value = u'is okay'
    index_settings[u'okay_setting'] = okay_setting_value

    settings = {
        u'index': index_settings,
        okay_setting_key: okay_setting_value
    }

    mappings = {
        u'a field': u'with config'
    }

    index = {
        u'some-index-name': {
            u'settings': settings,
            u'mappings': mappings
        }
    }

    cleaned = clean_index(index, False, False)

    # Settings are preserved
    cleaned_settings = cleaned.get(u'settings')
    assert okay_setting_key in cleaned_settings
    assert cleaned_settings[okay_setting_key] == okay_setting_value

    # Index settings are cleaned
    cleaned_index_settings = cleaned_settings.get(u'index')
    for key in DELETED_SETTINGS_KEYS:
        assert key not in cleaned_index_settings

    # Preserve index settings that shouldn't be removed
    assert okay_setting_key in cleaned_index_settings
    assert okay_setting_value == cleaned_index_settings[okay_setting_key]

    # Mappings are left as is
    assert cleaned.get(u'mappings') == mappings


def test_clean_index_skip_mapping():
    index = {
        u'settings': {u'index': _create_index_setting()},
        u'mappings': {u'some mapping': 'some value'}
    }

    cleaned = clean_index(dict(some_index_name=index), False, True)

    assert cleaned[u'settings'] == {u'index': {}}
    assert cleaned[u'mappings'] == {}


def test_clean_index_skip_settings():
    index = {
        u'settings': {u'index': _create_index_setting()},
        u'mappings': {u'some mapping': 'some value'}
    }

    cleaned = clean_index(dict(some_index_name=index), True, False)

    assert cleaned[u'settings'] == {}
    assert cleaned[u'mappings'] == index[u'mappings']


def test_clean_index_skip_settings_and_mappings():
    index = {
        u'settings': {u'index': _create_index_setting()},
        u'mappings': {u'some mapping': 'some value'}
    }

    cleaned = clean_index(dict(some_index_name=index), True, True)

    assert cleaned == {u'settings': {}, u'mappings': {}}


def _create_index_setting():
    index_settings = dict()
    for key in DELETED_SETTINGS_KEYS:
        index_settings[key] = u'something'
    return index_settings
