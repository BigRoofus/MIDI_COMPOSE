def select_notes_by_dissonance(self, notes):
	"""
	Select notes based on dissonance rules with key awareness:
	1. Analyze key context
	2. Always keep highest and lowest notes (unless unison/octave)
	3. Select most dissonant intervals first (considering key context)
	4. Limit to max_voices
	"""
	if len(notes) <= self.max_voices:
		return notes
		
	notes = sorted(set(notes))  # Remove duplicates and sort
	
	if len(notes) <= self.max_voices:
		return notes
	
	# Analyze key context for this chord
	key_analysis = self.analyze_key_context(notes)
	if key_analysis:
		self.current_key = key_analysis[:2]  # (root, mode)
		self.key_confidence = key_analysis[2]
	else:
		self.current_key = None
		self.key_confidence = 0.0
	
	selected = []
	
	# Always include lowest note (bass)
	bass_note = min(notes)
	selected.append(bass_note)
	
	# Check if highest note is not unison or octave with bass
	treble_note = max(notes)
	interval_to_bass = self.get_interval_from_root(bass_note, treble_note)
	
	if interval_to_bass != 0:  # Not unison (accounting for octave equivalence)
		selected.append(treble_note)
	
	# If we need more notes, select by dissonance (key-aware or fallback)
	if len(selected) < self.max_voices:
		remaining_notes = [n for n in notes if n not in selected]
		
		# Calculate dissonance scores for remaining notes
		note_scores = []
		for note in remaining_notes:
			# Use key-aware dissonance scoring
			score = self.get_key_aware_dissonance_score(bass_note, note, notes)
			note_scores.append((score, note))
		
		# Sort by dissonance (lower score = more dissonant = higher priority)
		note_scores.sort()
		
		# Add most dissonant notes until we reach max_voices
		for score, note in note_scores:
			if len(selected) < self.max_voices:
				selected.append(note)
			else:
				break
	
	return sorted(selected)
