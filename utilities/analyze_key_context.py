"""Key context analysis using Krumhansl-Schmuckler method
    Analyze the key context using note frequency analysis.
    Returns (root, mode, confidence) or None if atonal."""
	
from .Krumhansl_Schmuckler_scale import MAJOR_KEY_PROFILE, MINOR_KEY_PROFILE
from .calculate_key_correlations import calculate_key_correlation

def analyze_key_context(notes, time_window_ms=8000):
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
        correlation = calculate_key_correlation(pitch_profile, root, 'major')
        if correlation > best_correlation:
            best_correlation = correlation
            best_key = root
            best_mode = 'major'
        
        # Test minor key
        correlation = calculate_key_correlation(pitch_profile, root, 'minor')
        if correlation > best_correlation:
            best_correlation = correlation
            best_key = root
            best_mode = 'minor'
    
    # Raised confidence threshold - more conservative
    confidence_threshold = 0.65
    if best_correlation < confidence_threshold:
        return None  # Likely atonal
    
    return (best_key, best_mode, best_correlation)
