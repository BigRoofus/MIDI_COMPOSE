def get_key_aware_dissonance_score(self, root_note, note, context_notes):
	"""
	Get dissonance score considering key context and user preference.
	Higher score = more dissonant (what we want to keep for dissonant preference).
	"""
	interval = self.get_interval_from_root(root_note, note)
	
	# If we have key context, use it
	if self.current_key and self.key_confidence > 0.6:
		key_root, mode = self.current_key[:2]
		base_score = self.get_key_contextual_dissonance(note, key_root, mode, interval)
	else:
		# Use original dissonance ranking
		if interval in self.DISSONANCE_RANKING:
			# Lower index = more dissonant, so invert the score
			base_score = list(self.DISSONANCE_RANKING.keys()).index(interval)
		else:
			base_score = 12  # Unknown interval, least priority
	
	# Adjust score based on consonance preference
	# consonance_preference: -10 (most dissonant) to 10 (most consonant)
	if self.consonance_preference < 0:
		# Prefer dissonant intervals - invert the score
		adjusted_score = 15 - base_score
	elif self.consonance_preference > 0:
		# Prefer consonant intervals - keep original scoring
		adjusted_score = base_score
	else:
		# Neutral - keep original
		adjusted_score = base_score
	
	# Apply intensity of preference
	intensity = abs(self.consonance_preference) / 10.0
	if intensity > 0:
		# Amplify the preference
		if self.consonance_preference < 0:
			# For dissonant preference, boost dissonant scores more
			adjusted_score = int(adjusted_score * (1 + intensity))
		else:
			# For consonant preference, boost consonant scores more
			adjusted_score = int(adjusted_score * (1 + intensity * (15 - adjusted_score) / 15))
	
	return adjusted_score
