"""Calculate correlation between pitch profile and key template."""

from .Krumhansl_Schmuckler_scale import MAJOR_KEY_PROFILE, MINOR_KEY_PROFILE

def calculate_key_correlation(pitch_profile, root, mode):
    template = MAJOR_KEY_PROFILE if mode == 'major' else MINOR_KEY_PROFILE
	
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
