"""Convert key root and mode to readable name"""

def get_key_name(root, mode):
    key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return f"{key_names[root]} {mode}"
