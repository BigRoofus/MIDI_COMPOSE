#!/usr/bin/env python3
"""
MIDI Data Model - Refactored for pretty_midi
Enhanced version using pretty_midi as the foundation while maintaining MIDI_COMPOSE API
"""

import pretty_midi
import numpy as np
from typing import List, Dict, Optional, Tuple, Set, Iterator
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import copy
import bisect

class EventType(Enum):
    """MIDI event types for internal representation"""
    CONTROL_CHANGE = "control_change"
    PROGRAM_CHANGE = "program_change"
    PITCH_BEND = "pitch_bend"
    AFTERTOUCH = "aftertouch"

@dataclass
class MidiNote:
    """
    Enhanced MIDI note class that wraps pretty_midi.Note
    Provides backward compatibility with existing API while leveraging pretty_midi
    """
    start: float                    # Start time in seconds (pretty_midi standard)
    end: float                      # End time in seconds
    pitch: int                      # MIDI pitch (0-127)
    velocity: int = 64              # Velocity (0-127)
    selected: bool = False          # For UI selection state
    
    def __post_init__(self):
        """Ensure valid ranges"""
        self.pitch = max(0, min(127, self.pitch))
        self.velocity = max(0, min(127, self.velocity))
        self.start = max(0.0, self.start)
        self.end = max(self.start, self.end)
    
    @property
    def duration(self) -> float:
        """Duration in seconds"""
        return max(0.0, self.end - self.start)
    
    @duration.setter
    def duration(self, value: float):
        """Set duration, updating end time"""
        self.end = self.start + max(0.0, value)
    
    @property
    def pitch_class(self) -> int:
        """Get pitch class (0-11) for harmonic analysis"""
        return self.pitch % 12
    
    @property
    def start_time(self) -> float:
        """Backward compatibility property"""
        return self.start
    
    @start_time.setter
    def start_time(self, value: float):
        """Backward compatibility setter"""
        self.start = value
    
    @property
    def end_time(self) -> float:
        """Backward compatibility property"""
        return self.end
    
    @end_time.setter
    def end_time(self, value: float):
        """Backward compatibility setter"""
        self.end = value
    
    def overlaps(self, other: 'MidiNote') -> bool:
        """Check if this note overlaps with another note"""
        return not (self.end <= other.start or other.end <= self.start)
    
    def contains_time(self, time: float) -> bool:
        """Check if the given time falls within this note"""
        return self.start <= time < self.end
    
    def transpose(self, semitones: int):
        """Transpose note by semitones, clamping to valid MIDI range"""
        self.pitch = max(0, min(127, self.pitch + semitones))
    
    def to_pretty_midi_note(self) -> pretty_midi.Note:
        """Convert to pretty_midi.Note object"""
        return pretty_midi.Note(
            start=self.start,
            end=self.end,
            pitch=self.pitch,
            velocity=self.velocity
        )
    
    @classmethod
    def from_pretty_midi_note(cls, pm_note: pretty_midi.Note) -> 'MidiNote':
        """Create MidiNote from pretty_midi.Note"""
        return cls(
            start=pm_note.start,
            end=pm_note.end,
            pitch=pm_note.pitch,
            velocity=pm_note.velocity
        )
    
    def copy(self) -> 'MidiNote':
        """Create a deep copy of this note"""
        return MidiNote(
            start=self.start,
            end=self.end,
            pitch=self.pitch,
            velocity=self.velocity,
            selected=False  # Don't copy selection state
        )

@dataclass
class MidiEvent:
    """Represents non-note MIDI events (control changes, etc.)"""
    time: float                     # Time in seconds
    event_type: EventType
    channel: int = 0               # 0-15
    data1: int = 0                 # Controller number, program number, etc.
    data2: int = 0                 # Value
    
    def copy(self) -> 'MidiEvent':
        """Create a deep copy of this event"""
        return MidiEvent(
            time=self.time,
            event_type=self.event_type,
            channel=self.channel,
            data1=self.data1,
            data2=self.data2
        )

class MidiTrack:
    """
    Enhanced MIDI track that wraps pretty_midi.Instrument
    Maintains existing API while leveraging pretty_midi features
    """
    
    def __init__(self, name: str = "Untitled Track", program: int = 0, is_drum: bool = False):
        self.name = name
        self.program = program
        self.is_drum = is_drum
        
        # Create underlying pretty_midi instrument
        self._pm_instrument = pretty_midi.Instrument(
            program=program,
            is_drum=is_drum,
            name=name
        )
        
        # Our enhanced note objects (wrapping pretty_midi notes)
        self._notes: List[MidiNote] = []
        self.events: List[MidiEvent] = []
        
        # Track properties
        self.muted = False
        self.solo = False
        self.volume = 100           # 0-127
        self.pan = 64              # 0-127 (64 = center)
        
        # For UI state
        self.visible = True
        self.color = "#4A90E2"     # Default track color
        
        # Channel is derived from program for compatibility
        self.channel = program % 16
    
    @property
    def notes(self) -> List[MidiNote]:
        """Get all notes in the track"""
        return self._notes
    
    def add_note(self, note: MidiNote):
        """Add a note to the track"""
        self._notes.append(note)
        # Sync with pretty_midi instrument
        self._pm_instrument.notes.append(note.to_pretty_midi_note())
    
    def remove_note(self, note: MidiNote) -> bool:
        """Remove a note from the track. Returns True if found and removed."""
        try:
            index = self._notes.index(note)
            del self._notes[index]
            # Also remove from pretty_midi instrument
            del self._pm_instrument.notes[index]
            return True
        except (ValueError, IndexError):
            return False
    
    def add_event(self, event: MidiEvent):
        """Add an event to the track"""
        self.events.append(event)
        
        # Convert to pretty_midi control change if applicable
        if event.event_type == EventType.CONTROL_CHANGE:
            cc = pretty_midi.ControlChange(
                number=event.data1,
                value=event.data2,
                time=event.time
            )
            self._pm_instrument.control_changes.append(cc)
    
    def get_notes_at_time(self, time: float) -> List[MidiNote]:
        """Get all notes playing at the specified time"""
        return [note for note in self._notes if note.contains_time(time)]
    
    def get_notes_in_range(self, start_time: float, end_time: float) -> List[MidiNote]:
        """Get all notes that overlap with the specified time range"""
        return [note for note in self._notes 
                if note.start < end_time and note.end > start_time]
    
    def get_notes_in_pitch_range(self, low_pitch: int, high_pitch: int) -> List[MidiNote]:
        """Get all notes within the specified pitch range (inclusive)"""
        return [note for note in self._notes 
                if low_pitch <= note.pitch <= high_pitch]
    
    def quantize_notes(self, grid_size: float, strength: float = 1.0, selected_only: bool = False):
        """
        Quantize note start times to grid. 
        
        Args:
            grid_size: Grid size in seconds
            strength: Quantization strength (0.0-1.0)
            selected_only: Only quantize selected notes
        """
        for note in self._notes:
            if not selected_only or note.selected:
                grid_time = round(note.start / grid_size) * grid_size
                note.start = note.start + (grid_time - note.start) * strength
        
        self._sync_with_pretty_midi()
    
    def transpose_notes(self, semitones: int, selected_only: bool = False):
        """Transpose notes by semitones"""
        for note in self._notes:
            if not selected_only or note.selected:
                note.transpose(semitones)
        
        self._sync_with_pretty_midi()
    
    def get_selected_notes(self) -> List[MidiNote]:
        """Get all currently selected notes"""
        return [note for note in self._notes if note.selected]
    
    def select_all_notes(self):
        """Select all notes in the track"""
        for note in self._notes:
            note.selected = True
    
    def clear_selection(self):
        """Clear selection from all notes"""
        for note in self._notes:
            note.selected = False
    
    def get_time_bounds(self) -> Tuple[float, float]:
        """Get the start and end times of all content in the track"""
        if not self._notes and not self.events:
            return (0.0, 0.0)
        
        min_time = float('inf')
        max_time = 0.0
        
        for note in self._notes:
            min_time = min(min_time, note.start)
            max_time = max(max_time, note.end)
        
        for event in self.events:
            min_time = min(min_time, event.time)
            max_time = max(max_time, event.time)
        
        return (min_time if min_time != float('inf') else 0.0, max_time)
    
    def get_pitch_classes_at_time(self, time: float) -> Set[int]:
        """Get all pitch classes playing at specified time"""
        notes_at_time = self.get_notes_at_time(time)
        return {note.pitch_class for note in notes_at_time}
    
    def get_harmony_at_time(self, time: float) -> List[int]:
        """Get all pitches for harmony analysis at specified time"""
        notes_at_time = self.get_notes_at_time(time)
        return [note.pitch for note in notes_at_time]
    
    def _sync_with_pretty_midi(self):
        """Synchronize our notes with the underlying pretty_midi instrument"""
        # Clear and rebuild pretty_midi notes
        self._pm_instrument.notes.clear()
        for note in self._notes:
            self._pm_instrument.notes.append(note.to_pretty_midi_note())
    
    def copy(self) -> 'MidiTrack':
        """Create a deep copy of this track"""
        new_track = MidiTrack(
            name=f"{self.name} Copy", 
            program=self.program, 
            is_drum=self.is_drum
        )
        new_track._notes = [note.copy() for note in self._notes]
        new_track.events = [event.copy() for event in self.events]
        new_track.muted = self.muted
        new_track.solo = self.solo
        new_track.volume = self.volume
        new_track.pan = self.pan
        new_track.visible = self.visible
        new_track.color = self.color
        new_track._sync_with_pretty_midi()
        return new_track

class MidiDocument:
    """
    Enhanced document class built on pretty_midi.PrettyMIDI
    Provides advanced music analysis while maintaining existing API
    """
    
    def __init__(self):
        # Create underlying pretty_midi object
        self._pm = pretty_midi.PrettyMIDI()
        
        # Our enhanced track objects
        self.tracks: List[MidiTrack] = []
        
        # Document properties
        self.filename = "Untitled.mid"
        self.modified = False
        
        # Timeline state for UI
        self.current_position = 0.0    # Current position in seconds
        self.loop_start = 0.0
        self.loop_end = 0.0
        self.loop_enabled = False
        
        # Selection and editing state
        self.selected_tracks: Set[int] = set()
        self.clipboard: List[MidiNote] = []
    
    @property
    def tempo_bpm(self) -> float:
        """Get current tempo in BPM"""
        return self._pm.estimate_tempo() if self._pm.instruments else 120.0
    
    @property
    def time_signature(self) -> Tuple[int, int]:
        """Get current time signature"""
        if self._pm.time_signature_changes:
            ts = self._pm.time_signature_changes[0]
            return (ts.numerator, ts.denominator)
        return (4, 4)
    
    @property
    def key_signature(self) -> Tuple[int, bool]:
        """Get current key signature"""
        if self._pm.key_signature_changes:
            ks = self._pm.key_signature_changes[0]
            return (ks.key_number, ks.key_number >= 0)
        return (0, True)
    
    @property
    def resolution(self) -> int:
        """Get resolution (ticks per beat) - for backward compatibility"""
        return self._pm.resolution
    
    @property
    def ticks_per_beat(self) -> int:
        """Backward compatibility alias"""
        return self.resolution
    
    def add_track(self, track: Optional[MidiTrack] = None) -> MidiTrack:
        """Add a new track to the document"""
        if track is None:
            track = MidiTrack(
                name=f"Track {len(self.tracks) + 1}",
                program=len(self.tracks) % 128
            )
        
        self.tracks.append(track)
        self._pm.instruments.append(track._pm_instrument)
        self.modified = True
        return track
    
    def remove_track(self, track_index: int) -> bool:
        """Remove a track by index. Returns True if successful."""
        if 0 <= track_index < len(self.tracks):
            del self.tracks[track_index]
            del self._pm.instruments[track_index]
            
            # Update selected tracks
            self.selected_tracks.discard(track_index)
            self.selected_tracks = {
                i - 1 if i > track_index else i 
                for i in self.selected_tracks 
                if i != track_index
            }
            self.modified = True
            return True
        return False
    
    def get_all_notes_at_time(self, time: float) -> List[Tuple[MidiNote, int]]:
        """Get all notes playing at time across all tracks"""
        result = []
        for track_idx, track in enumerate(self.tracks):
            if not track.muted:
                notes = track.get_notes_at_time(time)
                result.extend([(note, track_idx) for note in notes])
        return result
    
    def get_chord_at_time(self, time: float) -> List[int]:
        """Get all pitches playing at the specified time (for harmony analysis)"""
        notes_and_tracks = self.get_all_notes_at_time(time)
        return [note.pitch for note, _ in notes_and_tracks]
    
    def get_pitch_classes_at_time(self, time: float) -> Set[int]:
        """Get all pitch classes at specified time across all tracks"""
        pitch_classes = set()
        for track in self.tracks:
            if not track.muted:
                pitch_classes.update(track.get_pitch_classes_at_time(time))
        return pitch_classes
    
    def get_time_bounds(self) -> Tuple[float, float]:
        """Get the overall start and end times of the document"""
        if not self.tracks:
            return (0.0, 0.0)
        
        min_time = float('inf')
        max_time = 0.0
        
        for track in self.tracks:
            track_start, track_end = track.get_time_bounds()
            min_time = min(min_time, track_start)
            max_time = max(max_time, track_end)
        
        return (min_time if min_time != float('inf') else 0.0, max_time)
    
    def seconds_to_beats(self, seconds: float) -> float:
        """Convert seconds to beats at current tempo"""
        return seconds * (self.tempo_bpm / 60.0)
    
    def beats_to_seconds(self, beats: float) -> float:
        """Convert beats to seconds at current tempo"""
        return beats * (60.0 / self.tempo_bpm)
    
    # Backward compatibility methods (convert between ticks and seconds)
    def ticks_to_seconds(self, ticks: int) -> float:
        """Convert ticks to seconds - backward compatibility"""
        beats = ticks / self.resolution
        return self.beats_to_seconds(beats)
    
    def seconds_to_ticks(self, seconds: float) -> int:
        """Convert seconds to ticks - backward compatibility"""
        beats = self.seconds_to_beats(seconds)
        return int(beats * self.resolution)
    
    def ticks_to_beats(self, ticks: int) -> float:
        """Convert ticks to beats - backward compatibility"""
        return ticks / self.resolution
    
    def beats_to_ticks(self, beats: float) -> int:
        """Convert beats to ticks - backward compatibility"""
        return int(beats * self.resolution)
    
    def quantize_all_tracks(self, grid_size: float, strength: float = 1.0, selected_only: bool = False):
        """Quantize all tracks to grid (grid_size in seconds)"""
        for track_idx, track in enumerate(self.tracks):
            if not selected_only or track_idx in self.selected_tracks:
                track.quantize_notes(grid_size, strength)
        self.modified = True
    
    def transpose_all_tracks(self, semitones: int, selected_only: bool = False):
        """Transpose all tracks by semitones"""
        for track_idx, track in enumerate(self.tracks):
            if not selected_only or track_idx in self.selected_tracks:
                track.transpose_notes(semitones)
        self.modified = True
    
    def copy_selected_notes(self):
        """Copy all selected notes to clipboard"""
        self.clipboard.clear()
        for track in self.tracks:
            selected_notes = track.get_selected_notes()
            self.clipboard.extend([note.copy() for note in selected_notes])
    
    def paste_notes_at_time(self, time: float, track_index: Optional[int] = None):
        """Paste clipboard notes at the specified time"""
        if not self.clipboard or not self.tracks:
            return
        
        if track_index is None:
            track_index = 0
        
        if track_index >= len(self.tracks):
            return
        
        target_track = self.tracks[track_index]
        
        # Find the earliest start time in clipboard
        earliest_time = min(note.start for note in self.clipboard)
        time_offset = time - earliest_time
        
        # Add offset notes to target track
        for note in self.clipboard:
            new_note = note.copy()
            new_note.start += time_offset
            new_note.end += time_offset
            target_track.add_note(new_note)
        
        self.modified = True
    
    # Advanced analysis methods using pretty_midi
    def estimate_key(self) -> Tuple[str, str]:
        """Estimate the key using pretty_midi's built-in analysis"""
        if not self._pm.instruments:
            return ("C", "major")
        
        # Get key estimate from pretty_midi
        key_number = self._pm.estimate_key()
        
        # Convert to readable format
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        if key_number < 12:
            return (key_names[key_number], "major")
        else:
            return (key_names[key_number - 12], "minor")
    
    def get_piano_roll_data(self, sampling_rate: int = 100) -> np.ndarray:
        """Get piano roll representation for analysis"""
        return self._pm.get_piano_roll(fs=sampling_rate)
    
    def get_chroma_vector(self, time: float) -> np.ndarray:
        """Get 12-dimensional chroma vector at specified time"""
        # Sample around the time point
        start_time = max(0, time - 0.1)
        end_time = time + 0.1
        
        chroma = np.zeros(12)
        for track in self.tracks:
            if track.muted:
                continue
            notes_in_range = track.get_notes_in_range(start_time, end_time)
            for note in notes_in_range:
                if note.contains_time(time):
                    chroma[note.pitch_class] += note.velocity / 127.0
        
        # Normalize
        if chroma.sum() > 0:
            chroma /= chroma.sum()
        
        return chroma
    
    @classmethod
    def from_midi_file(cls, filename: str) -> 'MidiDocument':
        """Create MidiDocument from a MIDI file using pretty_midi"""
        doc = cls()
        doc.filename = filename
        
        try:
            # Load with pretty_midi
            pm = pretty_midi.PrettyMIDI(filename)
            doc._pm = pm
            
            # Convert instruments to our track format
            for pm_instrument in pm.instruments:
                track = MidiTrack(
                    name=pm_instrument.name or f"Track {len(doc.tracks) + 1}",
                    program=pm_instrument.program,
                    is_drum=pm_instrument.is_drum
                )
                
                # Convert notes
                for pm_note in pm_instrument.notes:
                    note = MidiNote.from_pretty_midi_note(pm_note)
                    track._notes.append(note)
                
                # Convert control changes to events
                for cc in pm_instrument.control_changes:
                    event = MidiEvent(
                        time=cc.time,
                        event_type=EventType.CONTROL_CHANGE,
                        data1=cc.number,
                        data2=cc.value
                    )
                    track.events.append(event)
                
                doc.tracks.append(track)
            
            doc.modified = False
            return doc
            
        except Exception as e:
            print(f"Error loading MIDI file {filename}: {e}")
            return doc
    
    def to_midi_file(self, filename: Optional[str] = None) -> bool:
        """Save document as MIDI file using pretty_midi"""
        if filename is None:
            filename = self.filename
        
        try:
            # Sync all tracks with pretty_midi
            for track in self.tracks:
                track._sync_with_pretty_midi()
            
            # Save using pretty_midi
            self._pm.write(filename)
            self.filename = filename
            self.modified = False
            return True
            
        except Exception as e:
            print(f"Error saving MIDI file {filename}: {e}")
            return False
    
    def synthesize(self, sample_rate: int = 22050) -> np.ndarray:
        """Synthesize audio using pretty_midi (requires fluidsynth)"""
        return self._pm.synthesize(fs=sample_rate)