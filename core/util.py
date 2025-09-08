def analyze_key_context(self, notes, time_window_ms=8000):
	"""
	Analyze the key context using note frequency analysis.
	Returns (root, mode, confidence) or None if atonal.
	"""
	if not notes:
		return None
		
	# Count note frequencies (convert to pitch classes)
	pitch_counts = [0] * 12
	for note in notes:
		pitch_class = note % 12
		pitch_counts[pitch_class] += 1
	
	# Normalize counts
	total_notes = sum(pitch_counts)
	if total_notes == 0:
		return None
	
	pitch_profile = [count / total_notes for count in pitch_counts]
	
	best_correlation = -1
	best_key = None
	best_mode = None
	
	# Test all 24 keys (12 major + 12 minor)
	for root in range(12):
		# Test major key
		correlation = self.calculate_key_correlation(pitch_profile, root, 'major')
		if correlation > best_correlation:
			best_correlation = correlation
			best_key = root
			best_mode = 'major'
		
		# Test minor key
		correlation = self.calculate_key_correlation(pitch_profile, root, 'minor')
		if correlation > best_correlation:
			best_correlation = correlation
			best_key = root
			best_mode = 'minor'
	
	# Raised confidence threshold - more conservative
	confidence_threshold = 0.65
	if best_correlation < confidence_threshold:
		return None  # Likely atonal
	
	return (best_key, best_mode, best_correlation)

def update_key_analysis(self, current_measure, detected_key):
	"""
	Update key analysis with stability checking.
	Only reports key changes that are sustained over multiple measures.
	"""
	# Add to buffer with measure number
	self.key_buffer.append((current_measure, detected_key))
	
	# Keep only recent detections (configurable window)
	self.key_buffer = [(m, k) for m, k in self.key_buffer if current_measure - m <= self.key_analysis_window]
	
	# Count occurrences of each key in recent measures
	key_counts = {}
	for measure, key in self.key_buffer:
		key_counts[key] = key_counts.get(key, 0) + 1
	
	# Find the most frequent key
	if key_counts:
		most_frequent_key = max(key_counts.items(), key=lambda x: x[1])
		frequent_key, count = most_frequent_key
		
		# Only consider it stable if seen in required minimum duration
		min_stability = max(self.min_key_duration, len(self.key_buffer) // 3 + 1)
		
		if count >= min_stability and frequent_key != self.last_stable_key:
			# We have a new stable key!
			if self.key_changes and frequent_key == self.key_changes[-1][1]:
				# Same as last reported key, just update the measure
				return
			
			# Find when this key period started
			start_measure = current_measure
			for measure, key in reversed(self.key_buffer):
				if key == frequent_key:
					start_measure = measure
				else:
					break
			
			# Record the key change
			self.key_changes.append((start_measure, frequent_key))
			self.last_stable_key = frequent_key

def calculate_key_correlation(self, pitch_profile, root, mode):
	"""Calculate correlation between pitch profile and key template."""
	template = self.MAJOR_KEY_PROFILE if mode == 'major' else self.MINOR_KEY_PROFILE
	
	# Rotate template to match the root
	rotated_template = template[root:] + template[:root]
	
	# Calculate Pearson correlation coefficient
	mean_profile = sum(pitch_profile) / len(pitch_profile)
	mean_template = sum(rotated_template) / len(rotated_template)
	
	numerator = sum((pitch_profile[i] - mean_profile) * (rotated_template[i] - mean_template) 
					for i in range(12))
	
	sum_sq_profile = sum((pitch_profile[i] - mean_profile) ** 2 for i in range(12))
	sum_sq_template = sum((rotated_template[i] - mean_template) ** 2 for i in range(12))
	
	denominator = (sum_sq_profile * sum_sq_template) ** 0.5
	
	if denominator == 0:
		return 0
	
	return numerator / denominator

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

def get_interval_from_root(self, root_note, note):
	"""Calculate semitone interval from root note."""
	return (note - root_note) % 12

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

def get_key_name(self, root, mode):
	"""Convert key root and mode to readable name."""
	key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
	return f"{key_names[root]} {mode}"