"""Music theory constants and basic functions"""

# Key names for display
KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Dissonance ranking from most to least dissonant
DISSONANCE_RANKING = {
    6: 'Tritone',           # Most dissonant
    10: 'Minor Seventh',
    11: 'Major Seventh', 
    1: 'Minor Second',
    2: 'Major Second',
    8: 'Minor Sixth',
    9: 'Major Sixth',
    3: 'Minor Third',
    4: 'Major Third',
    5: 'Perfect Fourth',
    7: 'Perfect Fifth',
    12: 'Octave'            # Least dissonant
}

# Key profiles for major and minor keys (Krumhansl-Schmuckler)
MAJOR_KEY_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_KEY_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

def get_key_name(root: int, mode: str) -> str:
    """Convert key root and mode to readable name"""
    return f"{KEY_NAMES[root]} {mode}"


"""Dissonance calculation and ranking"""
from typing import List, Optional, Tuple
from .music_theory import DISSONANCE_RANKING, get_key_name

class DissonanceCalculator:
    def __init__(self, max_voices: int = 4):
        self.max_voices = max_voices
        self.current_key = None
        self.key_confidence = 0.0
    
    def get_interval_from_root(self, root_note: int, note: int) -> int:
        """Calculate semitone interval from root note"""
        return (note - root_note) % 12
    
    def get_key_aware_dissonance_score(self, root_note: int, note: int, 
                                     context_notes: List[int], 
                                     current_key: Optional[Tuple] = None,
                                     key_confidence: float = 0.0,
                                     consonance_preference: int = 0) -> float:
        """Get dissonance score considering key context"""
        # Your existing dissonance scoring logic here
        pass
    
    def get_key_contextual_dissonance(self, note: int, key_root: int, 
                                    mode: str, interval_from_chord_root: int) -> float:
        """Calculate dissonance based on key context"""
        # Your existing key contextual logic here
        pass


import numpy as np
from typing import List, Optional, Tuple, Dict, Union
from dataclasses import dataclass
from collections import deque, defaultdict
from core.midi_data import MidiDocument, MidiNote 
from .music_theory import MAJOR_KEY_PROFILE, MINOR_KEY_PROFILE, get_key_name

@dataclass
class KeyAnalysisPoint:
    time: float
    measure: Optional[int]
    root: int
    mode: str
    confidence: float

@dataclass
class TonalityTransition:
    from_time: float
    to_time: float
    from_key: Tuple[int, str]
    to_key: Tuple[int, str]

class KeyAnalyzer:
    """Simple key analysis using Krumhansl-Schmuckler method"""
    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold
        self.key_buffer = []
        self.key_analysis_window = 4
        self.min_key_duration = 2
        self.last_stable_key = None
        self.key_changes = []

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

class SlidingWindowKeyAnalyzer:
    """Enhanced key analyzer with measure-by-measure sliding window analysis"""
    
    def __init__(self, 
                 base_window_measures: float = 2.0,
                 overlap_ratio: float = 0.5,
                 confidence_threshold: float = 0.65,
                 stability_threshold: int = 3,
                 adaptive_window: bool = True):
        self.base_window_measures = base_window_measures
        self.overlap_ratio = overlap_ratio
        self.confidence_threshold = confidence_threshold
        self.stability_threshold = stability_threshold
        self.adaptive_window = adaptive_window
        
        self.analysis_points = []
        self.stability_buffer = deque(maxlen=stability_threshold)
        self.current_stable_key = None
        self.key_transitions = []
        
    def analyze_by_measures(self, document: MidiDocument) -> List[KeyAnalysisPoint]:
        self.analysis_points = []
        self.stability_buffer.clear()
        self.current_stable_key = None
        
        measure_times = self._get_measure_times(document)
        if not measure_times:
            return self._fallback_time_based_analysis(document)
        
        windows = self._calculate_measure_windows(measure_times)
        
        for window_info in windows:
            analysis_point = self._analyze_window(document, window_info)
            if analysis_point:
                self.analysis_points.append(analysis_point)
                self._update_stability_tracking(analysis_point)
        
        self._smooth_key_analysis()
        return self.analysis_points
    
    def _get_measure_times(self, document: MidiDocument) -> List[Tuple[float, int]]:
        measure_times = []
        # Simplified measure time calculation
        start_time, end_time = document.get_time_bounds()
        estimated_measure_duration = 2.0  # Fallback to a fixed duration
        current_time = 0.0
        measure_number = 1
        while current_time < end_time:
            measure_times.append((current_time, measure_number))
            current_time += estimated_measure_duration
            measure_number += 1
        return measure_times
    
    def _calculate_measure_windows(self, measure_times: List[Tuple[float, int]]) -> List[Dict]:
        windows = []
        if len(measure_times) < 2: return windows
        step_measures = self.base_window_measures * (1 - self.overlap_ratio)
        i = 0
        while i < len(measure_times):
            window_start_time, start_measure = measure_times[i]
            window_size = self.base_window_measures
            target_end_measure = start_measure + window_size
            end_measure_index = next((j for j, mt in enumerate(measure_times[i:]) 
                                      if mt[1] >= target_end_measure), len(measure_times) - i - 1) + i
            end_time, end_measure = measure_times[min(end_measure_index, len(measure_times) - 1)]
            if end_time > window_start_time:
                windows.append({
                    'start_time': window_start_time, 'end_time': end_time,
                    'start_measure': start_measure, 'end_measure': end_measure,
                    'window_size_measures': window_size,
                    'center_time': (window_start_time + end_time) / 2
                })
            i = next((j for j, mt in enumerate(measure_times[i:]) 
                      if mt[1] >= start_measure + step_measures), len(measure_times) - i) + i
            if i >= len(measure_times): break
        return windows

    def _analyze_window(self, document: MidiDocument, window_info: Dict) -> Optional[KeyAnalysisPoint]:
        start_time, end_time = window_info['start_time'], window_info['end_time']
        pc_result = self._analyze_pitch_class_profile(document, start_time, end_time)
        if not pc_result: return None
        
        root, mode, confidence = pc_result
        return KeyAnalysisPoint(
            time=window_info['center_time'],
            measure=int(window_info['start_measure']),
            root=root, mode=mode, confidence=confidence
        )
    
    def _analyze_pitch_class_profile(self, document: MidiDocument,
                                       start_time: float, end_time: float) -> Optional[Tuple[int, str, float]]:
        pitch_weights = np.zeros(12)
        total_weight = 0.0
        
        for track in document.tracks:
            for note in track.notes:
                overlap_duration = max(0, min(note.end, end_time) - max(note.start, start_time))
                if overlap_duration > 0:
                    weight = overlap_duration * (note.velocity / 127.0)
                    pitch_weights[note.pitch % 12] += weight
                    total_weight += weight
        
        if total_weight == 0: return None
        pitch_profile = pitch_weights / total_weight
        
        best_correlation = -1
        best_key = None
        for root in range(12):
            correlation_major = self._calculate_key_correlation(pitch_profile, root, 'major')
            correlation_minor = self._calculate_key_correlation(pitch_profile, root, 'minor')
            if correlation_major > best_correlation:
                best_correlation = correlation_major
                best_key = (root, 'major')
            if correlation_minor > best_correlation:
                best_correlation = correlation_minor
                best_key = (root, 'minor')
        
        if best_key and best_correlation >= self.confidence_threshold:
            return (best_key[0], best_key[1], best_correlation)
        return None
    
    def _calculate_key_correlation(self, pitch_profile: np.ndarray, 
                                     root: int, mode: str) -> float:
        template = np.array(MAJOR_KEY_PROFILE if mode == 'major' else MINOR_KEY_PROFILE)
        rotated_template = np.roll(template, root)
        
        mean_profile = np.mean(pitch_profile)
        mean_template = np.mean(rotated_template)
        
        numerator = np.sum((pitch_profile - mean_profile) * (rotated_template - mean_template))
        profile_variance = np.sum((pitch_profile - mean_profile) ** 2)
        template_variance = np.sum((rotated_template - mean_template) ** 2)
        
        denominator = np.sqrt(profile_variance * template_variance)
        return numerator / denominator if denominator > 0 else 0
    
    def _update_stability_tracking(self, analysis_point: KeyAnalysisPoint):
        current_key = (analysis_point.root, analysis_point.mode)
        self.stability_buffer.append((current_key, analysis_point.confidence))
        
        if len(self.stability_buffer) == self.stability_threshold:
            key_counts = defaultdict(int)
            for key, _ in self.stability_buffer:
                key_counts[key] += 1
            
            most_common_key = max(key_counts, key=key_counts.get)
            
            if key_counts[most_common_key] >= self.stability_threshold - 1:
                if self.current_stable_key != most_common_key:
                    if self.current_stable_key is not None:
                        self.key_transitions.append(TonalityTransition(
                            from_time=self.analysis_points[-2].time,
                            to_time=analysis_point.time,
                            from_key=self.current_stable_key,
                            to_key=most_common_key
                        ))
                    self.current_stable_key = most_common_key
    
    def _smooth_key_analysis(self):
        if len(self.analysis_points) < 3: return
        for i in range(1, len(self.analysis_points) - 1):
            prev_key = (self.analysis_points[i-1].root, self.analysis_points[i-1].mode)
            curr_key = (self.analysis_points[i].root, self.analysis_points[i].mode)
            next_key = (self.analysis_points[i+1].root, self.analysis_points[i+1].mode)
            if prev_key == next_key and curr_key != prev_key:
                self.analysis_points[i].root = prev_key[0]
                self.analysis_points[i].mode = prev_key[1]

    def _fallback_time_based_analysis(self, document: MidiDocument) -> List[KeyAnalysisPoint]:
        analysis_points = []
        start_time, end_time = document.get_time_bounds()
        window_duration = 2.0
        step_duration = 1.0
        current_time = start_time
        while current_time < end_time:
            window_info = {'start_time': current_time, 'end_time': current_time + window_duration, 
                           'start_measure': None, 'center_time': current_time + window_duration / 2}
            analysis_point = self._analyze_window(document, window_info)
            if analysis_point:
                analysis_points.append(analysis_point)
            current_time += step_duration
        return analysis_points
    
    def get_key_transitions(self) -> List[TonalityTransition]:
        return self.key_transitions
