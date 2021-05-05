import logging

from esok.constants import UNKNOWN_ERROR

LOG = logging.getLogger(__name__)


def clean_index(index, skip_settings, skip_mapping):
    """ Cleans a mapping fetched from ES from settings that you cannot set yourself."""
    if len(index.keys()) > 1:
        LOG.error('Cannot unpack index mapping.')
        exit(UNKNOWN_ERROR)
    else:
        root_key = list(index.keys()).pop()

    index_root = index.get(root_key)

    # Remove meta fields that you can't set on your own.
    settings = index_root.get(u'settings')
    index_settings = settings.get(u'index')
    del index_settings[u'version']
    del index_settings[u'creation_date']
    del index_settings[u'uuid']
    del index_settings[u'provided_name']

    cleaned_mapping = {
        u'mappings': index_root.get(u'mappings') if not skip_mapping else {},
        u'settings': settings if not skip_settings else {}
    }
    return cleaned_mapping
