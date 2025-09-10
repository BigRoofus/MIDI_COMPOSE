"""
Enhanced Key Analysis - pretty_midi Integration
Advanced key detection using pretty_midi's built-in analysis plus custom enhancements
"""
import numpy as np
from typing import List, Optional, Tuple, Dict
from core.midi_data import MidiDocument, MidiNote
from utils.music_theory import MAJOR_KEY_PROFILE, MINOR_KEY_PROFILE, get_key_name

class EnhancedKeyAnalyzer:
    """Enhanced key analyzer using pretty_midi plus custom analysis"""
    
    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold
        self.key_buffer = []
        self.key_analysis_window = 4.0  # seconds
        self.min_key_duration = 2.0     # seconds
        self.last_stable_key = None
        self.key_changes = []
    
    def analyze_key_context(self, document: MidiDocument, 
                          start_time: float = 0.0, 
                          end_time: Optional[float] = None) -> Optional[Tuple[int, str, float]]:
        """
        Analyze key context from document using multiple methods
        
        Returns: (root, mode, confidence) or None if uncertain
        """
        if not document.tracks:
            return None
        
        if end_time is None:
            _, end_time = document.get_time_bounds()
        
        # Method 1: Use pretty_midi's built-in key estimation
        try:
            pm_key_estimate = document._pm.estimate_key()
            if pm_key_estimate < 12:
                pm_root = pm_key_estimate
                pm_mode = 'major'
            else:
                pm_root = pm_key_estimate - 12
                pm_mode = 'minor'
        except:
            pm_root, pm_mode = None, None
        
        # Method 2: Custom pitch class analysis
        custom_result = self._analyze_pitch_classes(document, start_time, end_time)
        
        # Method 3: Harmonic analysis at key points
        harmonic_result = self._analyze_harmonic_progression(document, start_time, end_time)
        
        # Combine results with weighting
        results = []
        if pm_root is not None:
            results.append((pm_root, pm_mode, 0.8))  # pretty_midi gets high weight
        if custom_result:
            results.append(custom_result)
        if harmonic_result:
            results.append(harmonic_result)
        
        if not results:
            return None
        
        # Find consensus or highest confidence result
        return self._combine_key_estimates(results)
    
    def _analyze_pitch_classes(self, document: MidiDocument, 
                             start_time: float, end_time: float) -> Optional[Tuple[int, str, float]]:
        """Custom pitch class analysis using Krumhansl-Schmuckler"""
        # Collect all notes in time range
        pitch_counts = np.zeros(12)
        total_duration = 0.0
        
        for track in document.tracks:
            if track.muted:
                continue
                
            for note in track.notes:
                if note.end <= start_time or note.start >= end_time:
                    continue
                
                # Calculate overlap with analysis window
                overlap_start = max(note.start, start_time)
                overlap_end = min(note.end, end_time)
                overlap_duration = overlap_end - overlap_start
                
                if overlap_duration > 0:
                    # Weight by duration and velocity
                    weight = overlap_duration * (note.velocity / 127.0)
                    pitch_counts[note.pitch_class] += weight
                    total_duration += overlap_duration
        
        if total_duration == 0:
            return None
        
        # Normalize pitch profile
        pitch_profile = pitch_counts / np.sum(pitch_counts)
        
        # Test against key profiles
        best_correlation = -1
        best_key = None
        best_mode = None
        
        for root in range(12):
            # Test major
            correlation = self._calculate_key_correlation(pitch_profile, root, 'major')
            if correlation > best_correlation:
                best_correlation = correlation
                best_key = root
                best_mode = 'major'
            
            # Test minor
            correlation = self._calculate_key_correlation(pitch_profile, root, 'minor')
            if correlation > best_correlation:
                best_correlation = correlation
                best_key = root
                best_mode = 'minor'
        
        if best_correlation < self.confidence_threshold:
            return None
        
        return (best_key, best_mode, best_correlation)
    
    def _analyze_harmonic_progression(self, document: MidiDocument,
                                    start_time: float, end_time: float) -> Optional[Tuple[int, str, float]]:
        """Analyze harmonic progression to determine key"""
        # Sample harmony at regular intervals
        sampling_rate = 4.0  # samples per second
        time_points = np.arange(start_time, end_time, 1.0 / sampling_rate)
        
        chord_progressions = []
        
        for time_point in time_points:
            chord = document.get_chord_at_time(time_point)
            if len(chord) >= 2:  # Need at least 2 notes for harmony
                # Convert to pitch classes and sort
                pc_chord = sorted(list(set(pitch % 12 for pitch in chord)))
                if len(pc_chord) >= 2:
                    chord_progressions.append(pc_chord)
        
        if not chord_progressions:
            return None
        
        # Analyze chord progressions for tonal center
        return self._find_tonal_center(chord_progressions)
    
    def _find_tonal_center(self, chord_progressions: List[List[int]]) -> Optional[Tuple[int, str, float]]:
        """Find tonal center from chord progressions"""
        # Simple approach: count root candidates
        root_candidates = np.zeros(12)
        
        for chord in chord_progressions:
            # Assume bass note (lowest) might be root
            if chord:
                root_candidates[chord[0]] += 1
            
            # Also consider typical chord intervals
            if len(chord) >= 3:
                # Look for triads
                for i in range(len(chord) - 2):
                    interval1 = (chord[i+1] - chord[i]) % 12
                    interval2 = (chord[i+2] - chord[i]) % 12
                    
                    # Major triad: 4, 7 semitones
                    if interval1 == 4 and interval2 == 7:
                        root_candidates[chord[i]] += 2  # Strong evidence
                    # Minor triad: 3, 7 semitones
                    elif interval1 == 3 and interval2 == 7:
                        root_candidates[chord[i]] += 2
        
        if np.sum(root_candidates) == 0:
            return None
        
        # Find most likely root
        most_likely_root = np.argmax(root_candidates)
        confidence = root_candidates[most_likely_root] / np.sum(root_candidates)
        
        # Determine major/minor by analyzing thirds
        major_evidence = 0
        minor_evidence = 0
        
        for chord in chord_progressions:
            for note in chord:
                interval = (note - most_likely_root) % 12
                if interval == 4:  # Major third
                    major_evidence += 1
                elif interval == 3:  # Minor third
                    minor_evidence += 1
        
        mode = 'major' if major_evidence >= minor_evidence else 'minor'
        
        return (most_likely_root, mode, confidence)
    
    def _combine_key_estimates(self, results: List[Tuple[int, str, float]]) -> Optional[Tuple[int, str, float]]:
        """Combine multiple key estimates into single result"""
        if not results:
            return None
        
        if len(results) == 1:
            return results[0]
        
        # Weight by confidence and look for consensus
        key_votes = {}
        total_weight = 0
        
        for root, mode, confidence in results:
            key = (root, mode)
            if key not in key_votes:
                key_votes[key] = 0
            key_votes[key] += confidence
            total_weight += confidence
        
        # Find highest weighted key
        best_key = max(key_votes.items(), key=lambda x: x[1])
        final_confidence = best_key[1] / total_weight
        
        return (best_key[0][0], best_key[0][1], final_confidence)
    
    def _calculate_key_correlation(self, pitch_profile: np.ndarray, 
                                 root: int, mode: str) -> float:
        """Calculate correlation between pitch profile and key template"""
        template = np.array(MAJOR_KEY_PROFILE if mode == 'major' else MINOR_KEY_PROFILE)
        
        # Rotate template to match the root
        rotated_template = np.roll(template, root)
        
        # Calculate Pearson correlation coefficient
        mean_profile = np.mean(pitch_profile)
        mean_template = np.mean(rotated_template)
        
        numerator = np.sum((pitch_profile - mean_profile) * (rotated_template - mean_template))
        
        sum_sq_profile = np.sum((pitch_profile - mean_profile) ** 2)
        sum_sq_template = np.sum((rotated_template - mean_template) ** 2)
        
        denominator = np.sqrt(sum_sq_profile * sum_sq_template)
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
    
    def analyze_key_changes(self, document: MidiDocument, 
                           window_size: float = 4.0) -> List[Tuple[float, int, str, float]]:
        """
        Analyze key changes over time
        
        Returns: List of (time, root, mode, confidence) tuples
        """
        if not document.tracks:
            return []
        
        start_time, end_time = document.get_time_bounds()
        if end_time <= start_time:
            return []
        
        # Analyze in overlapping windows
        window_step = window_size / 2  # 50% overlap
        time_points = np.arange(start_time, end_time - window_size, window_step)
        
        key_changes = []
        last_key = None
        
        for time_point in time_points:
            window_end = min(time_point + window_size, end_time)
            key_result = self.analyze_key_context(document, time_point, window_end)
            
            if key_result and key_result[2] >= self.confidence_threshold:
                current_key = (key_result[0], key_result[1])
                
                # Only record if key changed
                if current_key != last_key:
                    key_changes.append((time_point, key_result[0], key_result[1], key_result[2]))
                    last_key = current_key
        
        return key_changes
    
    def get_key_at_time(self, document: MidiDocument, time: float) -> Optional[Tuple[int, str, float]]:
        """Get the most likely key at a specific time point"""
        window_start = max(0, time - self.key_analysis_window / 2)
        window_end = time + self.key_analysis_window / 2
        
        return self.analyze_key_context(document, window_start, window_end)
    
    def analyze_modulations(self, document: MidiDocument) -> List[Dict]:
        """
        Detect modulations (key changes) with detailed analysis
        
        Returns: List of modulation events with analysis
        """
        key_changes = self.analyze_key_changes(document)
        
        if len(key_changes) < 2:
            return []
        
        modulations = []
        
        for i in range(1, len(key_changes)):
            prev_time, prev_root, prev_mode, prev_conf = key_changes[i-1]
            curr_time, curr_root, curr_mode, curr_conf = key_changes[i]
            
            # Calculate interval relationship
            interval = (curr_root - prev_root) % 12
            
            # Classify modulation type
            modulation_type = self._classify_modulation(
                prev_root, prev_mode, curr_root, curr_mode, interval
            )
            
            modulation = {
                'time': curr_time,
                'from_key': get_key_name(prev_root, prev_mode),
                'to_key': get_key_name(curr_root, curr_mode),
                'interval': interval,
                'type': modulation_type,
                'confidence': min(prev_conf, curr_conf)
            }
            
            modulations.append(modulation)
        
        return modulations
    
    def _classify_modulation(self, from_root: int, from_mode: str,
                           to_root: int, to_mode: str, interval: int) -> str:
        """Classify the type of modulation"""
        if from_mode == to_mode:
            # Same mode modulations
            if interval == 7:  # Perfect 5th up
                return "Dominant Modulation"
            elif interval == 5:  # Perfect 5th down (or 4th up)
                return "Subdominant Modulation"
            elif interval == 2:  # Whole step up
                return "Step-wise Up"
            elif interval == 10:  # Whole step down
                return "Step-wise Down"
            elif interval == 1:  # Half step up
                return "Chromatic Up"
            elif interval == 11:  # Half step down
                return "Chromatic Down"
            else:
                return f"Parallel {from_mode.title()}"
        else:
            # Mode change modulations
            if from_root == to_root:
                return f"{from_mode.title()} to {to_mode.title()} (Same Root)"
            elif interval == 3 and from_mode == 'major' and to_mode == 'minor':
                return "Relative Minor"
            elif interval == 9 and from_mode == 'minor' and to_mode == 'major':
                return "Relative Major"
            else:
                return f"{from_mode.title()} to {to_mode.title()}"
    
    def get_key_stability_analysis(self, document: MidiDocument) -> Dict:
        """
        Analyze overall key stability of the piece
        
        Returns: Dictionary with stability metrics
        """
        key_changes = self.analyze_key_changes(document)
        
        if not key_changes:
            return {
                'stability': 'unknown',
                'primary_key': None,
                'modulation_count': 0,
                'average_key_duration': 0,
                'stability_score': 0
            }
        
        # Find primary key (most prevalent)
        key_durations = {}
        total_duration = 0
        
        start_time, end_time = document.get_time_bounds()
        
        for i, (time, root, mode, conf) in enumerate(key_changes):
            key = get_key_name(root, mode)
            
            if i < len(key_changes) - 1:
                duration = key_changes[i + 1][0] - time
            else:
                duration = end_time - time
            
            if key not in key_durations:
                key_durations[key] = 0
            key_durations[key] += duration
            total_duration += duration
        
        primary_key = max(key_durations.items(), key=lambda x: x[1])[0] if key_durations else None
        primary_key_duration = key_durations.get(primary_key, 0) if primary_key else 0
        
        # Calculate stability metrics
        modulation_count = len(key_changes) - 1
        average_key_duration = total_duration / len(key_changes) if key_changes else 0
        stability_score = primary_key_duration / total_duration if total_duration > 0 else 0
        
        # Classify stability
        if stability_score >= 0.8:
            stability = 'very stable'
        elif stability_score >= 0.6:
            stability = 'stable'
        elif stability_score >= 0.4:
            stability = 'moderately stable'
        else:
            stability = 'unstable'
        
        return {
            'stability': stability,
            'primary_key': primary_key,
            'modulation_count': modulation_count,
            'average_key_duration': average_key_duration,
            'stability_score': stability_score,
            'key_distribution': key_durations
        }
    
    def analyze_chord_functions(self, document: MidiDocument, 
                              time: float, key_root: int, key_mode: str) -> List[str]:
        """
        Analyze chord functions at a specific time within a given key
        
        Returns: List of possible chord function names
        """
        chord_pitches = document.get_chord_at_time(time)
        if len(chord_pitches) < 2:
            return []
        
        # Convert to pitch classes relative to key
        chord_pcs = sorted(list(set(pitch % 12 for pitch in chord_pitches)))
        
        # Calculate intervals from key root
        intervals = [(pc - key_root) % 12 for pc in chord_pcs]
        intervals.sort()
        
        # Common chord functions in major keys
        major_functions = {
            frozenset([0, 4, 7]): ['I', 'Tonic'],
            frozenset([2, 5, 9]): ['ii', 'Supertonic'],
            frozenset([4, 7, 11]): ['iii', 'Mediant'],
            frozenset([5, 9, 0]): ['IV', 'Subdominant'],
            frozenset([7, 11, 2]): ['V', 'Dominant'],
            frozenset([9, 0, 4]): ['vi', 'Submediant'],
            frozenset([11, 2, 5]): ['vii°', 'Leading Tone']
        }
        
        # Common chord functions in minor keys
        minor_functions = {
            frozenset([0, 3, 7]): ['i', 'Tonic'],
            frozenset([2, 5, 8]): ['ii°', 'Supertonic'],
            frozenset([3, 7, 10]): ['III', 'Mediant'],
            frozenset([5, 8, 0]): ['iv', 'Subdominant'],
            frozenset([7, 11, 2]): ['V', 'Dominant'],
            frozenset([8, 0, 3]): ['VI', 'Submediant'],
            frozenset([10, 2, 5]): ['VII', 'Subtonic']
        }
        
        functions = major_functions if key_mode == 'major' else minor_functions
        interval_set = frozenset(intervals)
        
        # Look for exact matches first
        if interval_set in functions:
            return functions[interval_set]
        
        # Look for subset matches (incomplete chords)
        matches = []
        for chord_set, function_names in functions.items():
            if interval_set.issubset(chord_set) or chord_set.issubset(interval_set):
                matches.extend(function_names)
        
        return matches if matches else ['Unknown']