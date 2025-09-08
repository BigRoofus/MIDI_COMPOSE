"""Calculate semitone interval from root note"""

def get_interval_from_root(root_note, note):
    return (note - root_note) % 12
