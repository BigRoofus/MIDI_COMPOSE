"""
This file contains all music theory and finctions
"""
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from collections import deque, defaultdict
import numpy as np

KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

DISSONANCE_RANKING = {
    6: 'Tritone', 10: 'Minor Seventh', 11: 'Major Seventh', 
    1: 'Minor Second', 2: 'Major Second', 8: 'Minor Sixth',
    9: 'Major Sixth', 3: 'Minor Third', 4: 'Major Third',
    5: 'Perfect Fourth', 7: 'Perfect Fifth', 12: 'Octave'
}

MAJOR_KEY_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_KEY_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

@dataclass
class MidiNote:
    pitch: int
    velocity: int
    start: float
    end: float

@dataclass
class MidiTrack:
    notes: List[MidiNote]

@dataclass
class MidiDocument:
    tracks: List[MidiTrack]
    
    def get_time_bounds(self) -> Tuple[float, float]:
        all_notes = [note for track in self.tracks for note in track.notes]
        if not all_notes:
            return 0.0, 0.0
        return min(n.start for n in all_notes), max(n.end for n in all_notes)

def get_key_name(root: int, mode: str) -> str:
    return f"{KEY_NAMES[root]} {mode.capitalize()}"

class DissonanceCalculator:
    def __init__(self, max_voices: int = 4):
        self.max_voices = max_voices
        self.current_key = None
        self.key_confidence = 0.0
    
    def get_interval_from_root(self, root_note: int, note: int) -> int:
        return (note - root_note) % 12
    
    def get_key_aware_dissonance_score(self, root_note: int, note: int, context_notes: List[int], current_key: Optional[Tuple] = None, key_confidence: float = 0.0, consonance_preference: int = 0) -> float:
        # Pass (implementation not provided)
        pass
    
    def get_key_contextual_dissonance(self, note: int, key_root: int, mode: str, interval_from_chord_root: int) -> float:
        # Pass (implementation not provided)
        pass

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

class KeyAnalyzerBase:
    def _calculate_key_correlation(self, pitch_profile: np.ndarray, root: int, mode: str) -> float:
        template = np.array(MAJOR_KEY_PROFILE if mode == 'major' else MINOR_KEY_PROFILE)
        rotated_template = np.roll(template, root)
        
        numerator = np.sum((pitch_profile - np.mean(pitch_profile)) * (rotated_template - np.mean(rotated_template)))
        denominator = np.sqrt(np.sum((pitch_profile - np.mean(pitch_profile)) ** 2) * np.sum((rotated_template - np.mean(rotated_template)) ** 2))
        return numerator / denominator if denominator > 0 else 0

    def _analyze_pitch_class_profile(self, pitch_weights: np.ndarray) -> Optional[Tuple[int, str, float]]:
        if not np.sum(pitch_weights):
            return None
        
        pitch_profile = pitch_weights / np.sum(pitch_weights)
        
        best_key = None
        best_correlation = -1

        for root in range(12):
            for mode in ['major', 'minor']:
                correlation = self._calculate_key_correlation(pitch_profile, root, mode)
                if correlation > best_correlation:
                    best_correlation = correlation
                    best_key = (root, mode)

        return (best_key[0], best_key[1], best_correlation) if best_key else None

class KeyAnalyzer(KeyAnalyzerBase):
    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold
        
    def analyze_key_context(self, notes: List[int]) -> Optional[Tuple[int, str, float]]:
        if not notes:
            return None
        
        pitch_counts = np.zeros(12)
        for note in notes:
            pitch_counts[note % 12] += 1
        
        result = self._analyze_pitch_class_profile(pitch_counts)
        return result if result and result[2] >= self.confidence_threshold else None

class SlidingWindowKeyAnalyzer(KeyAnalyzerBase):
    def __init__(self, base_window_measures: float = 2.0, overlap_ratio: float = 0.5, confidence_threshold: float = 0.65, stability_threshold: int = 3, adaptive_window: bool = True):
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
        self.analysis_points.clear()
        self.stability_buffer.clear()
        self.current_stable_key = None
        self.key_transitions.clear()
        
        measure_times = self._get_measure_times(document)
        if not measure_times:
            return self._fallback_time_based_analysis(document)
        
        windows = self._calculate_measure_windows(measure_times)
        
        for window_info in windows:
            if analysis_point := self._analyze_window(document, window_info):
                self.analysis_points.append(analysis_point)
                self._update_stability_tracking(analysis_point)
        
        self._smooth_key_analysis()
        return self.analysis_points

    def get_key_transitions(self) -> List[TonalityTransition]:
        return self.key_transitions

    def _get_measure_times(self, document: MidiDocument) -> List[Tuple[float, int]]:
        measure_times, current_time, measure_number = [], 0.0, 1
        _, end_time = document.get_time_bounds()
        estimated_measure_duration = 2.0
        while current_time < end_time:
            measure_times.append((current_time, measure_number))
            current_time += estimated_measure_duration
            measure_number += 1
        return measure_times

    def _calculate_measure_windows(self, measure_times: List[Tuple[float, int]]) -> List[Dict]:
        if len(measure_times) < 2:
            return []
        
        windows, i = [], 0
        step_measures = self.base_window_measures * (1 - self.overlap_ratio)
        
        while i < len(measure_times):
            window_start_time, start_measure = measure_times[i]
            target_end_measure = start_measure + self.base_window_measures
            end_measure_index = next((j for j, mt in enumerate(measure_times[i:]) if mt[1] >= target_end_measure), len(measure_times) - i - 1) + i
            end_time, _ = measure_times[min(end_measure_index, len(measure_times) - 1)]
            
            if end_time > window_start_time:
                windows.append({'start_time': window_start_time, 'end_time': end_time, 'start_measure': start_measure, 'center_time': (window_start_time + end_time) / 2})
            
            i = next((j for j, mt in enumerate(measure_times[i:]) if mt[1] >= start_measure + step_measures), len(measure_times) - i) + i
            if i >= len(measure_times): break
        return windows

    def _analyze_window(self, document: MidiDocument, window_info: Dict) -> Optional[KeyAnalysisPoint]:
        start_time, end_time, center_time = window_info['start_time'], window_info['end_time'], window_info['center_time']
        
        pitch_weights = np.zeros(12)
        for track in document.tracks:
            for note in track.notes:
                overlap = max(0, min(note.end, end_time) - max(note.start, start_time))
                if overlap > 0:
                    pitch_weights[note.pitch % 12] += overlap * (note.velocity / 127.0)
        
        result = self._analyze_pitch_class_profile(pitch_weights)
        
        if result and result[2] >= self.confidence_threshold:
            root, mode, confidence = result
            return KeyAnalysisPoint(time=center_time, measure=int(window_info['start_measure']), root=root, mode=mode, confidence=confidence)
        return None
    
    def _update_stability_tracking(self, analysis_point: KeyAnalysisPoint):
        current_key = (analysis_point.root, analysis_point.mode)
        self.stability_buffer.append((current_key, analysis_point.confidence))
        
        if len(self.stability_buffer) == self.stability_threshold:
            key_counts = defaultdict(int)
            if not self.stability_buffer: return
            for key, _ in self.stability_buffer: key_counts[key] += 1
            
            most_common_key = max(key_counts, key=key_counts.get)
            
            if key_counts[most_common_key] >= self.stability_threshold - 1 and self.current_stable_key != most_common_key:
                if self.current_stable_key is not None:
                    self.key_transitions.append(TonalityTransition(from_time=self.analysis_points[-2].time, to_time=analysis_point.time, from_key=self.current_stable_key, to_key=most_common_key))
                self.current_stable_key = most_common_key

    def _smooth_key_analysis(self):
        if len(self.analysis_points) < 3: return
        for i in range(1, len(self.analysis_points) - 1):
            prev_key = (self.analysis_points[i-1].root, self.analysis_points[i-1].mode)
            next_key = (self.analysis_points[i+1].root, self.analysis_points[i+1].mode)
            if prev_key == next_key and (self.analysis_points[i].root, self.analysis_points[i].mode) != prev_key:
                self.analysis_points[i].root, self.analysis_points[i].mode = prev_key

    def _fallback_time_based_analysis(self, document: MidiDocument) -> List[KeyAnalysisPoint]:
        analysis_points, start_time, end_time = [], *document.get_time_bounds()
        window_duration, step_duration = 2.0, 2.0 * (1 - self.overlap_ratio)
        current_time = start_time
        
        while current_time < end_time:
            window_info = {'start_time': current_time, 'end_time': current_time + window_duration, 'start_measure': None, 'center_time': current_time + window_duration / 2}
            if analysis_point := self._analyze_window(document, window_info):
                analysis_points.append(analysis_point)
            current_time += step_duration
        return analysis_points