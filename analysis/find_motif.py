#!/usr/bin/env python3
"""
MIDI Motif Detection and Analysis System
Finds and analyzes musical motifs in MIDI files using multiple detection algorithms.
"""

import sys
import os
from typing import List, Dict, Tuple, Set, Optional, NamedTuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import itertools
import math
from enum import Enum

# Add the parent directory to the path to import our core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.midi_data import MidiDocument, MidiTrack, MidiNote
except ImportError:
    print("Error: Could not import core MIDI modules. Make sure you're running from the correct directory.")
    sys.exit(1)

class MotifType(Enum):
    """Types of motifs that can be detected"""
    RHYTHMIC = "rhythmic"
    MELODIC = "melodic"
    HARMONIC = "harmonic"
    COMBINED = "combined"

class TransformationType(Enum):
    """Types of transformations applied to motifs"""
    IDENTITY = "identity"
    TRANSPOSITION = "transposition"
    INVERSION = "inversion"
    RETROGRADE = "retrograde"
    RETROGRADE_INVERSION = "retrograde_inversion"
    AUGMENTATION = "augmentation"
    DIMINUTION = "diminution"

@dataclass
class MotifNote:
    """Simplified note representation for motif analysis"""
    pitch: int
    start_time: int
    duration: int
    velocity: int
    
    @property
    def pitch_class(self) -> int:
        return self.pitch % 12
    
    def transpose(self, semitones: int) -> 'MotifNote':
        """Return transposed copy"""
        return MotifNote(
            pitch=self.pitch + semitones,
            start_time=self.start_time,
            duration=self.duration,
            velocity=self.velocity
        )

@dataclass
class MotifInstance:
    """Represents a single occurrence of a motif"""
    notes: List[MotifNote]
    start_time: int
    end_time: int
    track_index: int
    transformation: TransformationType = TransformationType.IDENTITY
    transformation_data: Dict = field(default_factory=dict)
    
    @property
    def duration(self) -> int:
        return self.end_time - self.start_time
    
    @property
    def pitch_span(self) -> int:
        if not self.notes:
            return 0
        pitches = [n.pitch for n in self.notes]
        return max(pitches) - min(pitches)
    
    def get_pitch_contour(self) -> List[int]:
        """Get pitch contour as intervals between consecutive notes"""
        if len(self.notes) < 2:
            return []
        pitches = [n.pitch for n in self.notes]
        return [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]
    
    def get_rhythm_pattern(self, quantize_to: int = 120) -> List[int]:
        """Get quantized rhythm pattern"""
        if not self.notes:
            return []
        
        # Sort notes by start time
        sorted_notes = sorted(self.notes, key=lambda n: n.start_time)
        
        # Calculate inter-onset intervals and quantize
        intervals = []
        for i in range(len(sorted_notes) - 1):
            interval = sorted_notes[i+1].start_time - sorted_notes[i].start_time
            quantized = round(interval / quantize_to) * quantize_to
            intervals.append(quantized)
        
        return intervals

@dataclass
class Motif:
    """Represents a musical motif with all its instances"""
    motif_id: str
    motif_type: MotifType
    instances: List[MotifInstance] = field(default_factory=list)
    prototype: Optional[MotifInstance] = None
    significance_score: float = 0.0
    
    @property
    def frequency(self) -> int:
        return len(self.instances)
    
    @property
    def tracks_spanned(self) -> Set[int]:
        return set(instance.track_index for instance in self.instances)
    
    @property
    def average_duration(self) -> float:
        if not self.instances:
            return 0.0
        return sum(instance.duration for instance in self.instances) / len(self.instances)
    
    def get_transformations(self) -> Dict[TransformationType, int]:
        """Count instances by transformation type"""
        counts = Counter(instance.transformation for instance in self.instances)
        return dict(counts)

class MotifDetector:
    """Main class for detecting motifs in MIDI data"""
    
    def __init__(self, 
                 min_motif_length: int = 3,
                 max_motif_length: int = 12,
                 min_frequency: int = 3,
                 pitch_tolerance: int = 0,
                 rhythm_tolerance: int = 60,
                 enable_transformations: bool = True):
        """
        Initialize motif detector with parameters
        
        Args:
            min_motif_length: Minimum number of notes in a motif
            max_motif_length: Maximum number of notes in a motif
            min_frequency: Minimum number of occurrences to consider a motif
            pitch_tolerance: Tolerance for pitch matching (semitones)
            rhythm_tolerance: Tolerance for rhythm matching (ticks)
            enable_transformations: Whether to detect transformed motifs
        """
        self.min_motif_length = min_motif_length
        self.max_motif_length = max_motif_length
        self.min_frequency = min_frequency
        self.pitch_tolerance = pitch_tolerance
        self.rhythm_tolerance = rhythm_tolerance
        self.enable_transformations = enable_transformations
        
        self.detected_motifs: List[Motif] = []
        self.motif_counter = 0
    
    def detect_motifs(self, document: MidiDocument) -> List[Motif]:
        """
        Detect all motifs in a MIDI document
        
        Args:
            document: MidiDocument to analyze
            
        Returns:
            List of detected motifs
        """
        print("🔍 Starting motif detection...")
        
        self.detected_motifs.clear()
        self.motif_counter = 0
        
        # Extract note sequences from all tracks
        note_sequences = self._extract_note_sequences(document)
        
        if not note_sequences:
            print("   No note sequences found")
            return []
        
        print(f"   Extracted {len(note_sequences)} note sequences")
        
        # Detect different types of motifs
        melodic_motifs = self._detect_melodic_motifs(note_sequences)
        rhythmic_motifs = self._detect_rhythmic_motifs(note_sequences)
        
        if self.enable_transformations:
            transformed_motifs = self._detect_transformed_motifs(note_sequences)
            self.detected_motifs.extend(transformed_motifs)
        
        self.detected_motifs.extend(melodic_motifs)
        self.detected_motifs.extend(rhythmic_motifs)
        
        # Calculate significance scores
        self._calculate_significance_scores()
        
        # Filter by minimum frequency
        self.detected_motifs = [m for m in self.detected_motifs if m.frequency >= self.min_frequency]
        
        # Sort by significance score
        self.detected_motifs.sort(key=lambda m: m.significance_score, reverse=True)
        
        print(f"   Found {len(self.detected_motifs)} significant motifs")
        return self.detected_motifs
    
    def _extract_note_sequences(self, document: MidiDocument) -> List[Tuple[List[MotifNote], int]]:
        """Extract note sequences from all tracks"""
        sequences = []
        
        for track_idx, track in enumerate(document.tracks):
            if not track.notes:
                continue
            
            # Sort notes by start time
            sorted_notes = sorted(track.notes, key=lambda n: n.start_time)
            
            # Convert to MotifNote objects
            motif_notes = []
            for note in sorted_notes:
                motif_note = MotifNote(
                    pitch=note.pitch,
                    start_time=note.start_time,
                    duration=note.duration,
                    velocity=note.velocity
                )
                motif_notes.append(motif_note)
            
            sequences.append((motif_notes, track_idx))
        
        return sequences
    
    def _detect_melodic_motifs(self, note_sequences: List[Tuple[List[MotifNote], int]]) -> List[Motif]:
        """Detect motifs based on melodic patterns (pitch contours)"""
        print("   Detecting melodic motifs...")
        
        motifs = []
        pattern_instances = defaultdict(list)
        
        for notes, track_idx in note_sequences:
            # Generate all possible subsequences
            for length in range(self.min_motif_length, min(len(notes) + 1, self.max_motif_length + 1)):
                for i in range(len(notes) - length + 1):
                    subsequence = notes[i:i+length]
                    
                    # Get pitch contour as pattern
                    if len(subsequence) < 2:
                        continue
                    
                    contour = self._get_pitch_contour(subsequence)
                    pattern_key = tuple(contour)
                    
                    # Create motif instance
                    instance = MotifInstance(
                        notes=subsequence,
                        start_time=subsequence[0].start_time,
                        end_time=subsequence[-1].start_time + subsequence[-1].duration,
                        track_index=track_idx
                    )
                    
                    pattern_instances[pattern_key].append(instance)
        
        # Convert patterns with sufficient instances to motifs
        for pattern, instances in pattern_instances.items():
            if len(instances) >= self.min_frequency:
                motif_id = f"MEL_{self.motif_counter:03d}"
                self.motif_counter += 1
                
                motif = Motif(
                    motif_id=motif_id,
                    motif_type=MotifType.MELODIC,
                    instances=instances,
                    prototype=instances[0]  # Use first instance as prototype
                )
                motifs.append(motif)
        
        return motifs
    
    def _detect_rhythmic_motifs(self, note_sequences: List[Tuple[List[MotifNote], int]]) -> List[Motif]:
        """Detect motifs based on rhythmic patterns"""
        print("   Detecting rhythmic motifs...")
        
        motifs = []
        pattern_instances = defaultdict(list)
        
        for notes, track_idx in note_sequences:
            # Generate all possible subsequences
            for length in range(self.min_motif_length, min(len(notes) + 1, self.max_motif_length + 1)):
                for i in range(len(notes) - length + 1):
                    subsequence = notes[i:i+length]
                    
                    # Get rhythm pattern
                    rhythm = self._get_rhythm_pattern(subsequence)
                    if not rhythm:
                        continue
                    
                    pattern_key = tuple(rhythm)
                    
                    # Create motif instance
                    instance = MotifInstance(
                        notes=subsequence,
                        start_time=subsequence[0].start_time,
                        end_time=subsequence[-1].start_time + subsequence[-1].duration,
                        track_index=track_idx
                    )
                    
                    pattern_instances[pattern_key].append(instance)
        
        # Convert patterns with sufficient instances to motifs
        for pattern, instances in pattern_instances.items():
            if len(instances) >= self.min_frequency:
                motif_id = f"RHY_{self.motif_counter:03d}"
                self.motif_counter += 1
                
                motif = Motif(
                    motif_id=motif_id,
                    motif_type=MotifType.RHYTHMIC,
                    instances=instances,
                    prototype=instances[0]
                )
                motifs.append(motif)
        
        return motifs
    
    def _detect_transformed_motifs(self, note_sequences: List[Tuple[List[MotifNote], int]]) -> List[Motif]:
        """Detect motifs that appear with transformations (transposition, inversion, etc.)"""
        print("   Detecting transformed motifs...")
        
        motifs = []
        pattern_groups = defaultdict(lambda: defaultdict(list))
        
        for notes, track_idx in note_sequences:
            for length in range(self.min_motif_length, min(len(notes) + 1, self.max_motif_length + 1)):
                for i in range(len(notes) - length + 1):
                    subsequence = notes[i:i+length]
                    
                    if len(subsequence) < 2:
                        continue
                    
                    # Get normalized patterns for different transformations
                    base_contour = tuple(self._get_pitch_contour(subsequence))
                    
                    instance = MotifInstance(
                        notes=subsequence,
                        start_time=subsequence[0].start_time,
                        end_time=subsequence[-1].start_time + subsequence[-1].duration,
                        track_index=track_idx
                    )
                    
                    # Identity
                    pattern_groups[base_contour][TransformationType.IDENTITY].append(instance)
                    
                    # Inversion (negate all intervals)
                    inverted_contour = tuple(-interval for interval in base_contour)
                    inv_instance = self._create_transformed_instance(instance, TransformationType.INVERSION)
                    pattern_groups[inverted_contour][TransformationType.INVERSION].append(inv_instance)
                    
                    # Retrograde (reverse the pattern)
                    retrograde_contour = tuple(reversed(base_contour))
                    retro_instance = self._create_transformed_instance(instance, TransformationType.RETROGRADE)
                    pattern_groups[retrograde_contour][TransformationType.RETROGRADE].append(retro_instance)
                    
                    # Retrograde inversion
                    retro_inv_contour = tuple(reversed(inverted_contour))
                    retro_inv_instance = self._create_transformed_instance(instance, TransformationType.RETROGRADE_INVERSION)
                    pattern_groups[retro_inv_contour][TransformationType.RETROGRADE_INVERSION].append(retro_inv_instance)
        
        # Group related transformations and create motifs
        processed_patterns = set()
        
        for base_pattern, transformations in pattern_groups.items():
            if base_pattern in processed_patterns:
                continue
            
            # Collect all instances across transformations
            all_instances = []
            for transform_type, instances in transformations.items():
                for instance in instances:
                    instance.transformation = transform_type
                    all_instances.append(instance)
            
            if len(all_instances) >= self.min_frequency:
                motif_id = f"TRA_{self.motif_counter:03d}"
                self.motif_counter += 1
                
                motif = Motif(
                    motif_id=motif_id,
                    motif_type=MotifType.COMBINED,
                    instances=all_instances,
                    prototype=all_instances[0]
                )
                motifs.append(motif)
                
                # Mark related patterns as processed
                processed_patterns.add(base_pattern)
                for transform_type in transformations:
                    if transform_type != TransformationType.IDENTITY:
                        processed_patterns.add(base_pattern)
        
        return motifs
    
    def _create_transformed_instance(self, original: MotifInstance, transformation: TransformationType) -> MotifInstance:
        """Create a transformed copy of a motif instance"""
        return MotifInstance(
            notes=original.notes.copy(),
            start_time=original.start_time,
            end_time=original.end_time,
            track_index=original.track_index,
            transformation=transformation
        )
    
    def _get_pitch_contour(self, notes: List[MotifNote]) -> List[int]:
        """Get pitch contour as intervals between consecutive notes"""
        if len(notes) < 2:
            return []
        return [notes[i+1].pitch - notes[i].pitch for i in range(len(notes)-1)]
    
    def _get_rhythm_pattern(self, notes: List[MotifNote], quantize_to: int = 120) -> List[int]:
        """Get quantized rhythm pattern"""
        if len(notes) < 2:
            return []
        
        # Calculate inter-onset intervals and quantize
        intervals = []
        for i in range(len(notes) - 1):
            interval = notes[i+1].start_time - notes[i].start_time
            quantized = round(interval / quantize_to) * quantize_to
            intervals.append(quantized)
        
        return intervals
    
    def _calculate_significance_scores(self):
        """Calculate significance scores for all detected motifs"""
        if not self.detected_motifs:
            return
        
        # Calculate various factors that contribute to significance
        max_frequency = max(m.frequency for m in self.detected_motifs)
        max_tracks = max(len(m.tracks_spanned) for m in self.detected_motifs)
        
        for motif in self.detected_motifs:
            # Frequency factor (more occurrences = more significant)
            frequency_factor = motif.frequency / max_frequency
            
            # Track span factor (appears in more tracks = more significant)
            track_factor = len(motif.tracks_spanned) / max_tracks if max_tracks > 0 else 0
            
            # Length factor (longer motifs are generally more significant)
            avg_length = sum(len(instance.notes) for instance in motif.instances) / len(motif.instances)
            length_factor = min(avg_length / 8.0, 1.0)  # Cap at 8 notes
            
            # Transformation variety factor (motifs with more transformations are interesting)
            transformations = motif.get_transformations()
            transformation_factor = min(len(transformations) / 4.0, 1.0)  # Cap at 4 types
            
            # Combined score
            motif.significance_score = (
                frequency_factor * 0.4 +
                track_factor * 0.3 +
                length_factor * 0.2 +
                transformation_factor * 0.1
            )

class MotifAnalyzer:
    """Analyzes and reports on detected motifs"""
    
    def __init__(self, motifs: List[Motif]):
        self.motifs = motifs
    
    def generate_report(self) -> str:
        """Generate a comprehensive text report of detected motifs"""
        if not self.motifs:
            return "No motifs detected."
        
        report = []
        report.append("🎵 MIDI MOTIF ANALYSIS REPORT")
        report.append("=" * 50)
        report.append("")
        
        # Summary statistics
        total_motifs = len(self.motifs)
        motif_types = Counter(m.motif_type for m in self.motifs)
        total_instances = sum(m.frequency for m in self.motifs)
        
        report.append("📊 SUMMARY STATISTICS")
        report.append(f"   Total motifs found: {total_motifs}")
        report.append(f"   Total motif instances: {total_instances}")
        report.append("")
        
        for motif_type, count in motif_types.items():
            report.append(f"   {motif_type.value.capitalize()} motifs: {count}")
        report.append("")
        
        # Top motifs
        report.append("🏆 TOP MOTIFS (by significance)")
        report.append("-" * 30)
        
        for i, motif in enumerate(self.motifs[:10], 1):  # Top 10
            report.append(f"\n{i}. {motif.motif_id} ({motif.motif_type.value.upper()})")
            report.append(f"   Frequency: {motif.frequency} occurrences")
            report.append(f"   Significance: {motif.significance_score:.3f}")
            report.append(f"   Tracks: {sorted(motif.tracks_spanned)}")
            
            if motif.prototype:
                report.append(f"   Length: {len(motif.prototype.notes)} notes")
                report.append(f"   Duration: {motif.prototype.duration} ticks")
                
                if motif.motif_type in [MotifType.MELODIC, MotifType.COMBINED]:
                    contour = motif.prototype.get_pitch_contour()
                    report.append(f"   Pitch contour: {contour}")
                
                if motif.motif_type in [MotifType.RHYTHMIC, MotifType.COMBINED]:
                    rhythm = motif.prototype.get_rhythm_pattern()
                    report.append(f"   Rhythm pattern: {rhythm}")
            
            # Transformation analysis
            if motif.motif_type == MotifType.COMBINED:
                transformations = motif.get_transformations()
                report.append("   Transformations:")
                for transform, count in transformations.items():
                    report.append(f"     {transform.value}: {count} instances")
        
        # Analysis by track
        report.append("\n\n📍 MOTIF DISTRIBUTION BY TRACK")
        report.append("-" * 35)
        
        track_motif_counts = defaultdict(int)
        track_instance_counts = defaultdict(int)
        
        for motif in self.motifs:
            for track_idx in motif.tracks_spanned:
                track_motif_counts[track_idx] += 1
                track_instances = sum(1 for instance in motif.instances 
                                   if instance.track_index == track_idx)
                track_instance_counts[track_idx] += track_instances
        
        for track_idx in sorted(track_motif_counts.keys()):
            report.append(f"\nTrack {track_idx + 1}:")
            report.append(f"   Unique motifs: {track_motif_counts[track_idx]}")
            report.append(f"   Total instances: {track_instance_counts[track_idx]}")
        
        return "\n".join(report)
    
    def export_motifs_to_midi(self, output_dir: str = "motif_exports") -> List[str]:
        """Export each motif's prototype as a separate MIDI file"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        exported_files = []
        
        for motif in self.motifs[:20]:  # Export top 20 motifs
            if not motif.prototype or not motif.prototype.notes:
                continue
            
            # Create a simple MIDI document for the motif
            doc = MidiDocument()
            track = doc.add_track()
            track.name = f"Motif {motif.motif_id}"
            
            # Add notes from prototype
            for motif_note in motif.prototype.notes:
                midi_note = MidiNote(
                    pitch=motif_note.pitch,
                    start_time=motif_note.start_time,
                    end_time=motif_note.start_time + motif_note.duration,
                    velocity=motif_note.velocity
                )
                track.add_note(midi_note)
            
            # Save to file
            filename = os.path.join(output_dir, f"{motif.motif_id}_prototype.mid")
            if doc.to_midi_file(filename):
                exported_files.append(filename)
        
        return exported_files


def select_midi_file():
    """GUI file picker for MIDI files"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        
        filename = filedialog.askopenfilename(
            title="Select MIDI file for motif analysis",
            filetypes=[("MIDI files", "*.mid *.MIDI"), ("All files", "*.*")]
        )
        
        root.destroy()
        return filename
    except ImportError:
        print("tkinter not available - using command line input")
        return input("Enter MIDI file path: ").strip()


def main():
    """Main function for motif detection"""
    print("🎵 MIDI Motif Detection System")
    print("=" * 40)
    print()
    
    # Select input file
    input_file = select_midi_file()
    
    if not input_file or not os.path.exists(input_file):
        print("❌ No valid file selected")
        return 1
    
    print(f"📁 Loading: {os.path.basename(input_file)}")
    
    # Load MIDI document
    try:
        document = MidiDocument.from_midi_file(input_file)
        print(f"   Tracks: {len(document.tracks)}")
        
        total_notes = sum(len(track.notes) for track in document.tracks)
        print(f"   Total notes: {total_notes}")
        
        if total_notes == 0:
            print("❌ No notes found in MIDI file")
            return 1
            
    except Exception as e:
        print(f"❌ Error loading MIDI file: {e}")
        return 1
    
    # Get detection parameters
    print("\n⚙️ Detection Parameters:")
    
    try:
        min_length = int(input("Minimum motif length (notes) [3]: ") or "3")
        max_length = int(input("Maximum motif length (notes) [8]: ") or "8")
        min_freq = int(input("Minimum frequency (occurrences) [3]: ") or "3")
        
        enable_transforms = input("Enable transformations (y/n) [y]: ").lower().startswith('y') or True
        
    except (ValueError, KeyboardInterrupt):
        print("Using default parameters...")
        min_length, max_length, min_freq = 3, 8, 3
        enable_transforms = True
    
    print(f"\n   Min length: {min_length}")
    print(f"   Max length: {max_length}")
    print(f"   Min frequency: {min_freq}")
    print(f"   Transformations: {'enabled' if enable_transforms else 'disabled'}")
    
    # Detect motifs
    detector = MotifDetector(
        min_motif_length=min_length,
        max_motif_length=max_length,
        min_frequency=min_freq,
        enable_transformations=enable_transforms
    )
    
    print("\n🔍 Analyzing motifs...")
    motifs = detector.detect_motifs(document)
    
    if not motifs:
        print("❌ No motifs found with the specified criteria")
        return 0
    
    # Generate and display report
    analyzer = MotifAnalyzer(motifs)
    report = analyzer.generate_report()
    
    print("\n" + report)
    
    # Save report to file
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    report_file = f"{base_name}_motif_analysis.txt"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n💾 Report saved to: {report_file}")
    except Exception as e:
        print(f"⚠️  Could not save report file: {e}")
    
    # Ask about exporting motifs
    if input("\nExport motif prototypes as MIDI files? (y/n) [n]: ").lower().startswith('y'):
        try:
            exported_files = analyzer.export_motifs_to_midi()
            if exported_files:
                print(f"✅ Exported {len(exported_files)} motif prototypes to 'motif_exports/' directory")
            else:
                print("❌ No motifs could be exported")
        except Exception as e:
            print(f"⚠️  Error exporting motifs: {e}")
    
    print("\n🎉 Motif analysis complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())