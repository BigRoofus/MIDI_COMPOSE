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