def get_key_contextual_dissonance(self, note, key_root, mode, interval_from_chord_root):
	"""
	Calculate dissonance based on key context.
	Returns higher scores for more dissonant notes (what we want to keep).
	"""
	# Get the note's position in the key
	note_in_key = (note - key_root) % 12
	
	# Define scale degrees for major and minor
	if mode == 'major':
		scale_degrees = [0, 2, 4, 5, 7, 9, 11]  # Major scale
		very_consonant = [0, 4, 7]  # Tonic triad
		consonant = [2, 9]  # 2nd and 6th scale degrees
	else:  # minor
		scale_degrees = [0, 2, 3, 5, 7, 8, 10]  # Natural minor scale
		very_consonant = [0, 3, 7]  # Minor triad
		consonant = [2, 8]  # 2nd and 6th scale degrees
	
	# Score based on relationship to key
	if note_in_key not in scale_degrees:
		# Chromatic note - very dissonant! Keep it!
		base_score = 0
	elif note_in_key in very_consonant:
		# Tonic triad member - least interesting
		base_score = 10
	elif note_in_key in consonant:
		# Other scale tones - moderate interest
		base_score = 7
	else:
		# Other scale degrees (like 7th, 4th) - more interesting
		base_score = 4
	
	# Adjust based on interval from chord root (your original logic)
	if interval_from_chord_root in self.DISSONANCE_RANKING:
		interval_score = list(self.DISSONANCE_RANKING.keys()).index(interval_from_chord_root)
		# Combine key context with interval dissonance
		return min(base_score + interval_score // 2, 15)
	
	return base_score
