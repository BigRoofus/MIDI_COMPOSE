"""Key analysis using Krumhansl-Schmuckler method"""
from utils.music_theory import MAJOR_KEY_PROFILE, MINOR_KEY_PROFILE, get_key_name

class KeyAnalyzer:
    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold
        self.key_buffer = []
        self.key_analysis_window = 4
        self.min_key_duration = 2
        self.last_stable_key = None
        self.key_changes = []
    # ... existing __init__ ...
    
    def analyze_key_context(self, notes: List[int]) -> Optional[Tuple[int, str, float]]:
        """Analyze key context from note list"""
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
        
        if best_correlation < self.confidence_threshold:
            return None  # Likely atonal
        
        return (best_key, best_mode, best_correlation)
    
    def calculate_key_correlation(self, pitch_profile: List[float], 
                                root: int, mode: str) -> float:
        """Calculate correlation between pitch profile and key template"""
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
