# where is this called? do we need this?
def update_key_analysis(current_measure, detected_key):
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