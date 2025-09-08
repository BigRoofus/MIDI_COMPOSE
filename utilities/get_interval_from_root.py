def get_interval_from_root(self, root_note, note):
	"""Calculate semitone interval from root note."""
	return (note - root_note) % 12
