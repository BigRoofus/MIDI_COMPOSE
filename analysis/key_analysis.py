"""
Enhanced Key Analysis - Sliding Window Implementation
Track key centers and tonalities from measure to measure with adaptive windows
"""
import numpy as np
from typing import List, Optional, Tuple, Dict, Union
from dataclasses import dataclass
from collections import deque, defaultdict
from core.midi_data import MidiDocument, MidiNote
from utils.music_theory import MAJOR_KEY_PROFILE, MINOR_KEY_PROFILE, get_key_name

@dataclass
class KeyAnalysisPoint:
    """Represents a key analysis at a specific point in time"""
    time: float
    measure: Optional[int]
    beat: Optional[float]
    root: int
    mode: str
    confidence: float
    analysis_method: str
    supporting_evidence: Dict
    window_size: float

@dataclass
class TonalityTransition:
    """Represents a transition between tonalities"""
    from_time: float
    to_time: float
    from_key: Tuple[int, str]
    to_key: Tuple[int, str]
    transition_strength: float
    pivot_chords: List[str]
    modulation_type: str

class SlidingWindowKeyAnalyzer:
    """Enhanced key analyzer with measure-by-measure sliding window analysis"""
    
    def __init__(self, 
                 base_window_measures: float = 2.0,
                 overlap_ratio: float = 0.5,
                 confidence_threshold: float = 0.65,
                 stability_threshold: int = 3,
                 adaptive_window: bool = True):
        """
        Initialize the sliding window analyzer
        
        Args:
            base_window_measures: Base window size in measures
            overlap_ratio: Overlap between consecutive windows (0.0 to 1.0)
            confidence_threshold: Minimum confidence for key detection
            stability_threshold: Number of consistent analyses needed for stability
            adaptive_window: Whether to adapt window size based on musical content
        """
        self.base_window_measures = base_window_measures
        self.overlap_ratio = overlap_ratio
        self.confidence_threshold = confidence_threshold
        self.stability_threshold = stability_threshold
        self.adaptive_window = adaptive_window
        
        # Analysis state
        self.analysis_points = []
        self.stability_buffer = deque(maxlen=stability_threshold)
        self.current_stable_key = None
        self.key_transitions = []
        
        # Adaptive parameters
        self.min_window_measures = 0.5
        self.max_window_measures = 8.0
        self.density_factor = 1.0
        self.harmony_factor = 1.0
    
    def analyze_by_measures(self, document: MidiDocument) -> List[KeyAnalysisPoint]:
        """
        Perform sliding window analysis aligned to measure boundaries
        
        Returns: List of key analysis points
        """
        self.analysis_points = []
        self.stability_buffer.clear()
        self.current_stable_key = None
        
        # Get measure information
        measure_times = self._get_measure_times(document)
        if not measure_times:
            return self._fallback_time_based_analysis(document)
        
        # Calculate sliding windows based on measures
        windows = self._calculate_measure_windows(measure_times)
        
        for window_info in windows:
            analysis_point = self._analyze_window(document, window_info)
            if analysis_point:
                self.analysis_points.append(analysis_point)
                self._update_stability_tracking(analysis_point)
        
        # Post-process to smooth out brief fluctuations
        self._smooth_key_analysis()
        
        return self.analysis_points
    
    def _get_measure_times(self, document: MidiDocument) -> List[Tuple[float, int]]:
        """Extract measure timing information from the document"""
        measure_times = []
        
        # Try to get time signature and tempo information
        time_signatures = getattr(document, 'time_signatures', [])
        tempo_changes = getattr(document, 'tempo_changes', [])
        
        # Default values
        current_time_sig = (4, 4)  # 4/4 time
        current_tempo = 120  # BPM
        
        if hasattr(document, '_pm') and document._pm:
            # Use pretty_midi's time signature and tempo information
            if document._pm.time_signature_changes:
                time_signatures = [(ts.time, ts.numerator, ts.denominator) 
                                 for ts in document._pm.time_signature_changes]
            
            if document._pm.tempo_changes:
                tempo_changes = [(tc.time, tc.tempo) for tc in document._pm.tempo_changes]
        
        # Calculate measure boundaries
        current_time = 0.0
        measure_number = 1
        
        start_time, end_time = document.get_time_bounds()
        
        # If we have time signatures, use them
        if time_signatures:
            ts_index = 0
            tempo_index = 0
            
            while current_time < end_time:
                # Update time signature if needed
                while (ts_index < len(time_signatures) and 
                       current_time >= time_signatures[ts_index][0]):
                    current_time_sig = (time_signatures[ts_index][1], 
                                      time_signatures[ts_index][2])
                    ts_index += 1
                
                # Update tempo if needed
                while (tempo_index < len(tempo_changes) and 
                       current_time >= tempo_changes[tempo_index][0]):
                    current_tempo = tempo_changes[tempo_index][1]
                    tempo_index += 1
                
                measure_times.append((current_time, measure_number))
                
                # Calculate measure duration
                beats_per_measure = current_time_sig[0]
                beat_duration = 60.0 / current_tempo  # seconds per beat
                measure_duration = beats_per_measure * beat_duration
                
                current_time += measure_duration
                measure_number += 1
        
        else:
            # Fallback: estimate from note patterns or use default
            estimated_measure_duration = self._estimate_measure_duration(document)
            
            while current_time < end_time:
                measure_times.append((current_time, measure_number))
                current_time += estimated_measure_duration
                measure_number += 1
        
        return measure_times
    
    def _estimate_measure_duration(self, document: MidiDocument) -> float:
        """Estimate measure duration from note patterns"""
        # Look for rhythmic patterns that might indicate measure boundaries
        note_onsets = []
        
        for track in document.tracks:
            if track.muted:
                continue
            for note in track.notes:
                note_onsets.append(note.start)
        
        if len(note_onsets) < 4:
            return 2.0  # Default 2-second measures
        
        note_onsets.sort()
        
        # Look for common intervals that might represent measures
        intervals = []
        for i in range(1, min(50, len(note_onsets))):  # Sample first 50 intervals
            intervals.append(note_onsets[i] - note_onsets[i-1])
        
        # Find mode of intervals (most common interval)
        interval_counts = defaultdict(int)
        for interval in intervals:
            # Round to nearest 0.1 second
            rounded_interval = round(interval, 1)
            interval_counts[rounded_interval] += 1
        
        if interval_counts:
            most_common_interval = max(interval_counts.items(), key=lambda x: x[1])[0]
            # Estimate measure duration as a multiple of common interval
            return most_common_interval * 4  # Assume 4 beats per measure
        
        return 2.0  # Fallback
    
    def _calculate_measure_windows(self, measure_times: List[Tuple[float, int]]) -> List[Dict]:
        """Calculate sliding window positions based on measures"""
        windows = []
        
        if len(measure_times) < 2:
            return windows
        
        step_measures = self.base_window_measures * (1 - self.overlap_ratio)
        
        i = 0
        while i < len(measure_times) - 1:
            window_start_time, start_measure = measure_times[i]
            
            # Determine window size (adaptive if enabled)
            if self.adaptive_window:
                window_size = self._calculate_adaptive_window_size(
                    measure_times, i, window_start_time
                )
            else:
                window_size = self.base_window_measures
            
            # Find end measure
            target_end_measure = start_measure + window_size
            end_time = None
            end_measure = start_measure
            
            for j in range(i, len(measure_times)):
                time, measure_num = measure_times[j]
                if measure_num >= target_end_measure:
                    end_time = time
                    end_measure = measure_num
                    break
            
            if end_time is None and len(measure_times) > i + 1:
                end_time = measure_times[-1][0]  # Use last measure
                end_measure = measure_times[-1][1]
            
            if end_time and end_time > window_start_time:
                window_info = {
                    'start_time': window_start_time,
                    'end_time': end_time,
                    'start_measure': start_measure,
                    'end_measure': end_measure,
                    'window_size_measures': window_size,
                    'center_time': (window_start_time + end_time) / 2,
                    'center_measure': (start_measure + end_measure) / 2
                }
                windows.append(window_info)
            
            # Move to next window position
            next_measure = start_measure + step_measures
            next_i = i
            for j in range(i + 1, len(measure_times)):
                if measure_times[j][1] >= next_measure:
                    next_i = j
                    break
            else:
                next_i = i + max(1, int(step_measures))
            
            i = min(next_i, i + 1)  # Ensure we make progress
        
        return windows
    
    def _calculate_adaptive_window_size(self, measure_times: List[Tuple[float, int]], 
                                      current_index: int, current_time: float) -> float:
        """Calculate adaptive window size based on musical content density"""
        # Sample a region around current position to assess density
        sample_start = max(0, current_index - 2)
        sample_end = min(len(measure_times), current_index + 5)
        
        if sample_end <= sample_start:
            return self.base_window_measures
        
        # This would need access to document - simplified version
        # In practice, you'd analyze note density, harmonic rhythm, etc.
        
        # For now, return base window size
        # TODO: Implement density analysis based on:
        # - Note density per measure
        # - Harmonic rhythm (chord change frequency)
        # - Melodic activity level
        
        return max(self.min_window_measures, 
                  min(self.max_window_measures, self.base_window_measures))
    
    def _analyze_window(self, document: MidiDocument, window_info: Dict) -> Optional[KeyAnalysisPoint]:
        """Analyze key within a specific window"""
        start_time = window_info['start_time']
        end_time = window_info['end_time']
        
        # Multi-method analysis
        results = []
        supporting_evidence = {}
        
        # Method 1: Pretty_midi estimation
        pm_result = self._get_prettymidi_key(document, start_time, end_time)
        if pm_result:
            results.append(pm_result)
            supporting_evidence['prettymidi'] = pm_result
        
        # Method 2: Pitch class profile analysis
        pc_result = self._analyze_pitch_class_profile(document, start_time, end_time)
        if pc_result:
            results.append(pc_result)
            supporting_evidence['pitch_class'] = pc_result
        
        # Method 3: Harmonic analysis
        harmonic_result = self._analyze_harmonic_context(document, start_time, end_time)
        if harmonic_result:
            results.append(harmonic_result)
            supporting_evidence['harmonic'] = harmonic_result
        
        # Method 4: Melodic analysis (new)
        melodic_result = self._analyze_melodic_context(document, start_time, end_time)
        if melodic_result:
            results.append(melodic_result)
            supporting_evidence['melodic'] = melodic_result
        
        if not results:
            return None
        
        # Combine results with intelligent weighting
        final_result = self._combine_analyses(results, window_info)
        if not final_result:
            return None
        
        root, mode, confidence, method = final_result
        
        return KeyAnalysisPoint(
            time=window_info['center_time'],
            measure=int(window_info['center_measure']),
            beat=None,  # Could be calculated if needed
            root=root,
            mode=mode,
            confidence=confidence,
            analysis_method=method,
            supporting_evidence=supporting_evidence,
            window_size=window_info['window_size_measures']
        )
    
    def _get_prettymidi_key(self, document: MidiDocument, 
                           start_time: float, end_time: float) -> Optional[Tuple[int, str, float]]:
        """Get key estimate from pretty_midi for a time range"""
        try:
            if not hasattr(document, '_pm') or not document._pm:
                return None
            
            # Create a temporary pretty_midi object for the time range
            pm_segment = document._pm.get_piano_roll(
                start_time=start_time, 
                end_time=end_time
            )
            
            if pm_segment.size == 0:
                return None
            
            # Use the original pretty_midi key estimation
            key_estimate = document._pm.estimate_key()
            
            if key_estimate < 12:
                return (key_estimate, 'major', 0.8)
            else:
                return (key_estimate - 12, 'minor', 0.8)
        
        except Exception:
            return None
    
    def _analyze_pitch_class_profile(self, document: MidiDocument,
                                   start_time: float, end_time: float) -> Optional[Tuple[int, str, float]]:
        """Enhanced pitch class profile analysis with duration weighting"""
        pitch_weights = np.zeros(12)
        total_weight = 0.0
        
        for track in document.tracks:
            if track.muted:
                continue
            
            for note in track.notes:
                # Calculate overlap with analysis window
                overlap_start = max(note.start, start_time)
                overlap_end = min(note.end, end_time)
                
                if overlap_end <= overlap_start:
                    continue
                
                overlap_duration = overlap_end - overlap_start
                
                # Weight by duration, velocity, and track importance
                track_weight = getattr(track, 'importance', 1.0)  # Could be set based on track type
                velocity_weight = note.velocity / 127.0
                duration_weight = overlap_duration
                
                total_weight_for_note = duration_weight * velocity_weight * track_weight
                pitch_weights[note.pitch % 12] += total_weight_for_note
                total_weight += total_weight_for_note
        
        if total_weight == 0:
            return None
        
        # Normalize
        pitch_profile = pitch_weights / total_weight
        
        # Find best key match using Krumhansl-Schmuckler profiles
        best_correlation = -1
        best_key = None
        
        for root in range(12):
            # Test major
            correlation = self._calculate_key_correlation(pitch_profile, root, 'major')
            if correlation > best_correlation:
                best_correlation = correlation
                best_key = (root, 'major')
            
            # Test minor
            correlation = self._calculate_key_correlation(pitch_profile, root, 'minor')
            if correlation > best_correlation:
                best_correlation = correlation
                best_key = (root, 'minor')
        
        if best_key and best_correlation >= self.confidence_threshold:
            return (best_key[0], best_key[1], best_correlation)
        
        return None
    
    def _analyze_harmonic_context(self, document: MidiDocument,
                                start_time: float, end_time: float) -> Optional[Tuple[int, str, float]]:
        """Analyze harmonic context with chord progression analysis"""
        # Sample chords at regular intervals
        sampling_interval = 0.25  # Every quarter second
        sample_times = np.arange(start_time, end_time, sampling_interval)
        
        chord_progressions = []
        chord_roots = defaultdict(int)
        
        for sample_time in sample_times:
            chord = document.get_chord_at_time(sample_time)
            if len(chord) >= 2:
                chord_pcs = sorted(list(set(pitch % 12 for pitch in chord)))
                chord_progressions.append(chord_pcs)
                
                # Identify likely root
                root_candidate = self._identify_chord_root(chord_pcs)
                if root_candidate is not None:
                    chord_roots[root_candidate] += 1
        
        if not chord_roots:
            return None
        
        # Find most common root
        most_common_root = max(chord_roots.items(), key=lambda x: x[1])[0]
        root_confidence = chord_roots[most_common_root] / sum(chord_roots.values())
        
        # Determine mode by analyzing chord qualities
        mode_evidence = self._analyze_chord_qualities(chord_progressions, most_common_root)
        mode = 'major' if mode_evidence > 0 else 'minor'
        
        return (most_common_root, mode, root_confidence * 0.9)  # Slightly lower weight
    
    def _analyze_melodic_context(self, document: MidiDocument,
                               start_time: float, end_time: float) -> Optional[Tuple[int, str, float]]:
        """Analyze melodic lines for tonal center"""
        melodic_notes = []
        
        # Extract melodic lines (highest notes, typically melody)
        for track in document.tracks:
            if track.muted or getattr(track, 'is_drum', False):
                continue
            
            track_notes = []
            for note in track.notes:
                if start_time <= note.start < end_time:
                    track_notes.append((note.start, note.pitch % 12, note.velocity))
            
            if track_notes:
                # Sort by time and take highest notes at each time point
                track_notes.sort()
                melodic_notes.extend(track_notes)
        
        if len(melodic_notes) < 4:
            return None
        
        # Analyze scale degrees and melodic patterns
        pitch_sequence = [note[1] for note in melodic_notes]
        
        # Look for scale patterns and cadential figures
        scale_evidence = defaultdict(float)
        
        for root in range(12):
            major_score = self._score_melodic_scale_fit(pitch_sequence, root, 'major')
            minor_score = self._score_melodic_scale_fit(pitch_sequence, root, 'minor')
            
            scale_evidence[(root, 'major')] = major_score
            scale_evidence[(root, 'minor')] = minor_score
        
        if scale_evidence:
            best_scale = max(scale_evidence.items(), key=lambda x: x[1])
            if best_scale[1] > 0.3:  # Threshold for melodic evidence
                return (best_scale[0][0], best_scale[0][1], best_scale[1])
        
        return None
    
    def _identify_chord_root(self, chord_pcs: List[int]) -> Optional[int]:
        """Identify the most likely root of a chord"""
        if len(chord_pcs) < 2:
            return None
        
        # Simple heuristic: lowest note is often the root
        # More sophisticated analysis could consider inversions
        return chord_pcs[0]
    
    def _analyze_chord_qualities(self, chord_progressions: List[List[int]], root: int) -> float:
        """Analyze chord qualities to determine major/minor tendency"""
        major_evidence = 0
        minor_evidence = 0
        
        for chord in chord_progressions:
            for note in chord:
                interval = (note - root) % 12
                if interval == 4:  # Major third
                    major_evidence += 1
                elif interval == 3:  # Minor third
                    minor_evidence += 1
        
        return major_evidence - minor_evidence
    
    def _score_melodic_scale_fit(self, pitch_sequence: List[int], root: int, mode: str) -> float:
        """Score how well a melodic line fits a given scale"""
        scale_degrees = [0, 2, 4, 5, 7, 9, 11] if mode == 'major' else [0, 2, 3, 5, 7, 8, 10]
        scale_pcs = [(root + degree) % 12 for degree in scale_degrees]
        
        total_notes = len(pitch_sequence)
        scale_notes = sum(1 for pitch in pitch_sequence if pitch in scale_pcs)
        
        return scale_notes / total_notes if total_notes > 0 else 0
    
    def _combine_analyses(self, results: List[Tuple[int, str, float]], 
                         window_info: Dict) -> Optional[Tuple[int, str, float, str]]:
        """Combine multiple analysis results with intelligent weighting"""
        if not results:
            return None
        
        # Weight results based on confidence and method reliability
        method_weights = {
            'prettymidi': 0.8,
            'pitch_class': 1.0,
            'harmonic': 0.9,
            'melodic': 0.7
        }
        
        weighted_votes = defaultdict(float)
        total_weight = 0
        
        for root, mode, confidence in results:
            key = (root, mode)
            weight = confidence  # Base weight is the confidence
            weighted_votes[key] += weight
            total_weight += weight
        
        if total_weight == 0:
            return None
        
        # Find the key with highest weighted vote
        best_key = max(weighted_votes.items(), key=lambda x: x[1])
        final_confidence = best_key[1] / total_weight
        
        # Determine primary analysis method
        method = "combined"
        
        return (best_key[0][0], best_key[0][1], final_confidence, method)
    
    def _calculate_key_correlation(self, pitch_profile: np.ndarray, 
                                 root: int, mode: str) -> float:
        """Calculate Pearson correlation with key profile"""
        template = np.array(MAJOR_KEY_PROFILE if mode == 'major' else MINOR_KEY_PROFILE)
        rotated_template = np.roll(template, root)
        
        # Pearson correlation
        mean_profile = np.mean(pitch_profile)
        mean_template = np.mean(rotated_template)
        
        numerator = np.sum((pitch_profile - mean_profile) * (rotated_template - mean_template))
        
        profile_variance = np.sum((pitch_profile - mean_profile) ** 2)
        template_variance = np.sum((rotated_template - mean_template) ** 2)
        
        denominator = np.sqrt(profile_variance * template_variance)
        
        return numerator / denominator if denominator > 0 else 0
    
    def _update_stability_tracking(self, analysis_point: KeyAnalysisPoint):
        """Update stability tracking for smooth key detection"""
        current_key = (analysis_point.root, analysis_point.mode)
        self.stability_buffer.append((current_key, analysis_point.confidence))
        
        # Check for stable key
        if len(self.stability_buffer) >= self.stability_threshold:
            # Count occurrences of each key in buffer
            key_counts = defaultdict(int)
            total_confidence = defaultdict(float)
            
            for key, confidence in self.stability_buffer:
                key_counts[key] += 1
                total_confidence[key] += confidence
            
            # Find most common key
            most_common_key = max(key_counts.items(), key=lambda x: x[1])
            
            if most_common_key[1] >= self.stability_threshold - 1:  # Allow one disagreement
                avg_confidence = total_confidence[most_common_key[0]] / most_common_key[1]
                if avg_confidence >= self.confidence_threshold:
                    if self.current_stable_key != most_common_key[0]:
                        # Key change detected
                        if self.current_stable_key is not None:
                            self._record_key_transition(
                                analysis_point.time, 
                                self.current_stable_key, 
                                most_common_key[0]
                            )
                        self.current_stable_key = most_common_key[0]
    
    def _record_key_transition(self, time: float, from_key: Tuple[int, str], to_key: Tuple[int, str]):
        """Record a key transition for later analysis"""
        transition = TonalityTransition(
            from_time=time - self.base_window_measures,  # Approximate
            to_time=time,
            from_key=from_key,
            to_key=to_key,
            transition_strength=0.8,  # Could be calculated
            pivot_chords=[],  # Could be analyzed
            modulation_type=self._classify_modulation_type(from_key, to_key)
        )
        self.key_transitions.append(transition)
    
    def _classify_modulation_type(self, from_key: Tuple[int, str], to_key: Tuple[int, str]) -> str:
        """Classify the type of modulation between keys"""
        from_root, from_mode = from_key
        to_root, to_mode = to_key
        
        interval = (to_root - from_root) % 12
        
        if from_mode == to_mode:
            if interval == 7:
                return "Dominant"
            elif interval == 5:
                return "Subdominant"
            elif interval == 2:
                return "Whole Step Up"
            elif interval == 10:
                return "Whole Step Down"
            else:
                return f"Parallel {from_mode.title()}"
        else:
            if from_root == to_root:
                return f"Modal ({from_mode} to {to_mode})"
            elif interval == 3 and from_mode == 'major' and to_mode == 'minor':
                return "Relative Minor"
            elif interval == 9 and from_mode == 'minor' and to_mode == 'major':
                return "Relative Major"
            else:
                return f"Mode Change"
    
    def _smooth_key_analysis(self):
        """Smooth out brief key fluctuations in the analysis"""
        if len(self.analysis_points) < 3:
            return
        
        # Simple smoothing: if a key appears for only one analysis point
        # and is surrounded by the same different key, change it
        for i in range(1, len(self.analysis_points) - 1):
            prev_key = (self.analysis_points[i-1].root, self.analysis_points[i-1].mode)
            curr_key = (self.analysis_points[i].root, self.analysis_points[i].mode)
            next_key = (self.analysis_points[i+1].root, self.analysis_points[i+1].mode)
            
            if prev_key == next_key and curr_key != prev_key:
                # Check if current analysis has low confidence
                if self.analysis_points[i].confidence < self.confidence_threshold + 0.1:
                    # Change to surrounding key
                    self.analysis_points[i].root = prev_key[0]
                    self.analysis_points[i].mode = prev_key[1]
                    self.analysis_points[i].analysis_method += " (smoothed)"
    
    def _fallback_time_based_analysis(self, document: MidiDocument) -> List[KeyAnalysisPoint]:
        """Fallback to time-based analysis if measure information unavailable"""
        analysis_points = []
        start_time, end_time = document.get_time_bounds()
        
        window_duration = 2.0  # 2 second windows
        step_duration = 1.0    # 1 second steps
        
        current_time = start_time
        measure_estimate = 1
        
        while current_time < end_time - window_duration:
            window_info = {
                'start_time': current_time,
                'end_time': current_time + window_duration,
                'start_measure': measure_estimate,
                'end_measure': measure_estimate + 1,
                'window_size_measures': 1.0,
                'center_time': current_time + window_duration / 2,
                'center_measure': measure_estimate + 0.5
            }
            
            analysis_point = self._analyze_window(document, window_info)
            if analysis_point:
                analysis_points.append(analysis_point)
            
            current_time += step_duration
            measure_estimate += 0.5  # Rough estimate
        
        return analysis_points
    
    def get_key_at_measure(self, measure: int) -> Optional[KeyAnalysisPoint]:
        """Get the key analysis for a specific measure"""
        for point in self.analysis_points:
            if point.measure and abs(point.measure - measure) < 0.5:
                return point
        return None
    
    def get_key_transitions(self) -> List[TonalityTransition]:
        """Get detected key transitions"""
        return self.key_transitions
    
    def get_stability_report(self) -> Dict:
        """Generate a report on key stability throughout the piece"""
        if not self.analysis_points:
            return {'error': 'No analysis points available'}
        
        # Count key occurrences
        key_counts = defaultdict(int)
        total_points = len(self.analysis_points)
        
        for point in self.analysis_points:
            key = get_key_name(point.root, point.mode)
            key_counts[key] += 1
        
        # Calculate stability metrics
        most_common_key = max(key_counts.items(), key=lambda x: x[1])
        stability_score = most_common_key[1] / total_points
        
        return {
            'primary_key': most_common_key[0],
            'stability_score': stability_score,
            'key_distribution': dict(key_counts),
            'total_analysis_points': total_points,
            'number_of_transitions': len(self.key_transitions),
            'average_confidence': np.mean([p.confidence for p in self.analysis_points]),
            'stability_classification': self._classify_stability(stability_score)
        }
    
    def _classify_stability(self, stability_score: float) -> str:
        """Classify overall stability based on score"""
        if stability_score >= 0.9:
            return "Very Stable"
        elif stability_score >= 0.7:
            return "Stable"
        elif stability_score >= 0.5:
            return "Moderately Stable"
        elif stability_score >= 0.3:
            return "Unstable"
        else:
            return "Highly Unstable"
    
    def export_analysis_timeline(self) -> List[Dict]:
        """Export analysis as a timeline for visualization"""
        timeline = []
        
        for point in self.analysis_points:
            timeline_entry = {
                'time': point.time,
                'measure': point.measure,
                'key': get_key_name(point.root, point.mode),
                'root': point.root,
                'mode': point.mode,
                'confidence': round(point.confidence, 3),
                'method': point.analysis_method,
                'window_size': point.window_size
            }
            timeline.append(timeline_entry)
        
        return timeline
    
    def analyze_measure_range(self, document: MidiDocument, 
                            start_measure: int, end_measure: int) -> Optional[KeyAnalysisPoint]:
        """Analyze a specific range of measures"""
        # Find time bounds for the measure range
        measure_times = self._get_measure_times(document)
        
        start_time = None
        end_time = None
        
        for time, measure in measure_times:
            if measure == start_measure:
                start_time = time
            elif measure == end_measure + 1:
                end_time = time
                break
        
        if start_time is None:
            return None
        
        if end_time is None:
            # Use document end time
            _, doc_end = document.get_time_bounds()
            end_time = doc_end
        
        # Create window info for the range
        window_info = {
            'start_time': start_time,
            'end_time': end_time,
            'start_measure': start_measure,
            'end_measure': end_measure,
            'window_size_measures': end_measure - start_measure + 1,
            'center_time': (start_time + end_time) / 2,
            'center_measure': (start_measure + end_measure) / 2
        }
        
        return self._analyze_window(document, window_info)


class MeasureSynchronizedAnalyzer(SlidingWindowKeyAnalyzer):
    """
    Specialized analyzer that synchronizes precisely with measure boundaries
    and provides beat-level analysis granularity
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.beat_level_analysis = kwargs.get('beat_level_analysis', False)
        self.sync_to_strong_beats = kwargs.get('sync_to_strong_beats', True)
    
    def analyze_with_beat_sync(self, document: MidiDocument) -> List[KeyAnalysisPoint]:
        """
        Perform analysis synchronized to beat boundaries
        """
        if not self.beat_level_analysis:
            return self.analyze_by_measures(document)
        
        # Get detailed timing information
        beat_times = self._get_beat_times(document)
        if not beat_times:
            return self.analyze_by_measures(document)  # Fallback
        
        # Create beat-synchronized windows
        windows = self._calculate_beat_windows(beat_times)
        
        analysis_points = []
        for window_info in windows:
            if self.sync_to_strong_beats and not self._is_strong_beat_window(window_info):
                continue
            
            analysis_point = self._analyze_window(document, window_info)
            if analysis_point:
                analysis_points.append(analysis_point)
        
        self.analysis_points = analysis_points
        return analysis_points
    
    def _get_beat_times(self, document: MidiDocument) -> List[Tuple[float, int, float]]:
        """Get beat timing information (time, measure, beat_in_measure)"""
        beat_times = []
        
        # Extract timing information
        time_signatures = []
        tempo_changes = []
        
        if hasattr(document, '_pm') and document._pm:
            if document._pm.time_signature_changes:
                time_signatures = [(ts.time, ts.numerator, ts.denominator) 
                                 for ts in document._pm.time_signature_changes]
            else:
                time_signatures = [(0.0, 4, 4)]  # Default 4/4
            
            if document._pm.tempo_changes:
                tempo_changes = [(tc.time, tc.tempo) for tc in document._pm.tempo_changes]
            else:
                tempo_changes = [(0.0, 120)]  # Default 120 BPM
        else:
            time_signatures = [(0.0, 4, 4)]
            tempo_changes = [(0.0, 120)]
        
        # Calculate beat positions
        current_time = 0.0
        current_measure = 1
        current_beat = 1.0
        
        start_time, end_time = document.get_time_bounds()
        
        ts_index = 0
        tempo_index = 0
        current_ts = time_signatures[0] if time_signatures else (0.0, 4, 4)
        current_tempo = tempo_changes[0][1] if tempo_changes else 120
        
        while current_time < end_time:
            # Update time signature if needed
            while (ts_index + 1 < len(time_signatures) and 
                   current_time >= time_signatures[ts_index + 1][0]):
                ts_index += 1
                current_ts = time_signatures[ts_index]
            
            # Update tempo if needed
            while (tempo_index + 1 < len(tempo_changes) and 
                   current_time >= tempo_changes[tempo_index + 1][0]):
                tempo_index += 1
                current_tempo = tempo_changes[tempo_index][1]
            
            beat_times.append((current_time, current_measure, current_beat))
            
            # Calculate next beat time
            beat_duration = 60.0 / current_tempo  # Duration of one quarter note
            current_time += beat_duration
            current_beat += 1
            
            # Check if we need to move to next measure
            beats_per_measure = current_ts[1]  # Numerator of time signature
            if current_beat > beats_per_measure:
                current_beat = 1
                current_measure += 1
        
        return beat_times
    
    def _calculate_beat_windows(self, beat_times: List[Tuple[float, int, float]]) -> List[Dict]:
        """Calculate windows aligned to beat boundaries"""
        windows = []
        
        if len(beat_times) < 8:  # Need at least 2 measures worth of beats
            return windows
        
        # Convert window size from measures to beats
        # Assume 4/4 time for simplicity (could be made more sophisticated)
        window_size_beats = self.base_window_measures * 4
        step_size_beats = window_size_beats * (1 - self.overlap_ratio)
        
        i = 0
        while i < len(beat_times) - window_size_beats:
            start_time, start_measure, start_beat = beat_times[i]
            
            # Find end of window
            end_index = min(i + int(window_size_beats), len(beat_times) - 1)
            end_time, end_measure, end_beat = beat_times[end_index]
            
            window_info = {
                'start_time': start_time,
                'end_time': end_time,
                'start_measure': start_measure,
                'end_measure': end_measure,
                'start_beat': start_beat,
                'end_beat': end_beat,
                'window_size_measures': (end_measure - start_measure) + (end_beat - start_beat) / 4,
                'center_time': (start_time + end_time) / 2,
                'center_measure': (start_measure + end_measure) / 2,
                'is_strong_beat': start_beat == 1.0  # Starts on downbeat
            }
            
            windows.append(window_info)
            
            # Move to next position
            i += max(1, int(step_size_beats))
        
        return windows
    
    def _is_strong_beat_window(self, window_info: Dict) -> bool:
        """Check if window starts on a strong beat"""
        return window_info.get('is_strong_beat', False)


class AdaptiveKeyTracker:
    """
    High-level interface that combines multiple analysis strategies
    and adapts to different musical styles and contexts
    """
    
    def __init__(self):
        self.base_analyzer = SlidingWindowKeyAnalyzer()
        self.beat_analyzer = MeasureSynchronizedAnalyzer(beat_level_analysis=True)
        self.style_detectors = {
            'classical': self._is_classical_style,
            'jazz': self._is_jazz_style,
            'pop': self._is_pop_style,
            'folk': self._is_folk_style
        }
    
    def analyze_with_adaptation(self, document: MidiDocument) -> Dict:
        """
        Perform adaptive analysis based on detected musical style
        """
        # Detect musical style
        detected_style = self._detect_musical_style(document)
        
        # Choose appropriate analysis strategy
        if detected_style == 'jazz':
            # Jazz often has complex harmony, use shorter windows
            analyzer = SlidingWindowKeyAnalyzer(
                base_window_measures=1.0,
                overlap_ratio=0.75,
                confidence_threshold=0.5  # Lower threshold for jazz
            )
        elif detected_style == 'classical':
            # Classical may have longer phrases, use longer windows
            analyzer = SlidingWindowKeyAnalyzer(
                base_window_measures=4.0,
                overlap_ratio=0.5,
                adaptive_window=True
            )
        elif detected_style in ['pop', 'folk']:
            # Pop/folk often has clear key centers, standard analysis
            analyzer = self.base_analyzer
        else:
            # Default analysis
            analyzer = self.base_analyzer
        
        # Perform analysis
        analysis_points = analyzer.analyze_by_measures(document)
        
        # Return comprehensive results
        return {
            'detected_style': detected_style,
            'analysis_points': analysis_points,
            'key_transitions': analyzer.get_key_transitions(),
            'stability_report': analyzer.get_stability_report(),
            'timeline': analyzer.export_analysis_timeline(),
            'analyzer_settings': {
                'window_measures': analyzer.base_window_measures,
                'overlap_ratio': analyzer.overlap_ratio,
                'confidence_threshold': analyzer.confidence_threshold
            }
        }
    
    def _detect_musical_style(self, document: MidiDocument) -> str:
        """Detect musical style based on various musical features"""
        # Simple style detection based on instrumentation and harmonic complexity
        # This could be much more sophisticated
        
        style_scores = {}
        
        for style, detector in self.style_detectors.items():
            style_scores[style] = detector(document)
        
        # Return style with highest score
        detected_style = max(style_scores.items(), key=lambda x: x[1])[0]
        
        # Require minimum confidence
        if style_scores[detected_style] < 0.3:
            return 'unknown'
        
        return detected_style
    
    def _is_classical_style(self, document: MidiDocument) -> float:
        """Detect classical music characteristics"""
        score = 0.0
        
        # Check for typical classical instrumentation
        if len(document.tracks) >= 2:  # Multi-part writing
            score += 0.3
        
        # Check for sustained notes (typical in classical)
        total_notes = 0
        long_notes = 0
        
        for track in document.tracks:
            for note in track.notes:
                total_notes += 1
                if note.duration > 1.0:  # Notes longer than 1 second
                    long_notes += 1
        
        if total_notes > 0:
            long_note_ratio = long_notes / total_notes
            score += long_note_ratio * 0.4
        
        # Other classical indicators could be added here
        
        return min(score, 1.0)
    
    def _is_jazz_style(self, document: MidiDocument) -> float:
        """Detect jazz music characteristics"""
        score = 0.0
        
        # Look for complex chords and frequent chord changes
        # This is a simplified detection
        
        # Check harmonic complexity by sampling chords
        complex_chords = 0
        total_chords = 0
        
        start_time, end_time = document.get_time_bounds()
        sample_times = np.arange(start_time, end_time, 0.5)
        
        for time in sample_times:
            chord = document.get_chord_at_time(time)
            if len(chord) >= 3:
                total_chords += 1
                if len(chord) >= 4:  # 7th chords and beyond
                    complex_chords += 1
        
        if total_chords > 0:
            complexity_ratio = complex_chords / total_chords
            score += complexity_ratio * 0.6
        
        return min(score, 1.0)
    
    def _is_pop_style(self, document: MidiDocument) -> float:
        """Detect pop music characteristics"""
        score = 0.0
        
        # Pop often has clear, simple chord progressions
        # and regular phrase structure
        
        # Check for 4/4 time signature (common in pop)
        if hasattr(document, '_pm') and document._pm:
            if document._pm.time_signature_changes:
                first_ts = document._pm.time_signature_changes[0]
                if first_ts.numerator == 4 and first_ts.denominator == 4:
                    score += 0.4
        
        # Check for moderate tempo (typical pop range)
        if hasattr(document, '_pm') and document._pm:
            if document._pm.tempo_changes:
                first_tempo = document._pm.tempo_changes[0].tempo
                if 90 <= first_tempo <= 140:  # Typical pop tempo range
                    score += 0.3
        
        return min(score, 1.0)
    
    def _is_folk_style(self, document: MidiDocument) -> float:
        """Detect folk music characteristics"""
        score = 0.0
        
        # Folk often has simple melodies and accompaniment
        # Usually fewer tracks
        
        if len(document.tracks) <= 3:  # Simple arrangement
            score += 0.4
        
        # Folk often has simple chord progressions
        # This could be detected by analyzing chord complexity
        
        return min(score, 1.0)