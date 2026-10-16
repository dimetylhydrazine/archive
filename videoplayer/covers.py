import hashlib

COVERS_DIR_NAME = '_covers'


def cover_rel_path(source_rel_path: str, ext: str = '.jpg') -> str:
    """
    Build a cover path relative to MEDIA_ROOT.

    The hash is computed from the source path, so the name is
    stable for a given source file and unique across different sources.
    """
    h = hashlib.sha1(source_rel_path.encode('utf-8')).hexdigest()
    return f'videos/{COVERS_DIR_NAME}/{h}{ext.lower()}'