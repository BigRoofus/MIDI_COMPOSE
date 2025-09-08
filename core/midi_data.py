#!/usr/bin/env python3
"""
MIDI Data Model - Core Classes
Comprehensive internal representation for MIDI data with editing capabilities.
"""

import mido
from typing import List, Dict, Optional, Tuple, Set, Iterator
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import copy
import bisect

class EventType(Enum):
    """MIDI event types for internal representation"""
    NOTE_ON = "note_on"
    NOTE_OFF = "note_off"
    CONTROL_CHANGE = "control_change"
    PROGRAM_CHANGE = "program_change"
    PITCH_BEND = "pitch_bend"
    AFTERTOUCH = "aftertouch"
    TEMPO = "set_tempo"
    TIME_SIGNATURE = "time_signature"
    KEY_SIGNATURE = "key_signature"

@dataclass
class MidiNote:
    """Represents a single MIDI note with start/end times"""
    pitch: int                   # 0-127
    start_time: int              # Absolute time in ticks
    end_time: int                # Absolute time in ticks
    velocity: int = 64           # 0-127
    channel: int = 0             # 0-15
    selected: bool = False       # For UI selection state
    
    @property
    def duration(self) -> int:
        """Duration in ticks"""
        return max(0, self.end_time - self.start_time)
    
    @duration.setter
    def duration(self, value: int):
        """Set duration, updating end_time"""
        self.end_time = self.start_time + max(0, value)
    
    @property
    def pitch_class(self) -> int:
        """Get pitch class (0-11) for harmonic analysis"""
        return self.pitch % 12
    
    def overlaps(self, other: 'MidiNote') -> bool:
        """Check if this note overlaps with another note"""
        return not (self.end_time <= other.start_time or other.end_time <= self.start_time)
    
    def contains_time(self, time: int) -> bool:
        """Check if the given time falls within this note"""
        return self.start_time <= time < self.end_time
    
    def transpose(self, semitones: int):
        """Transpose note by semitones, clamping to valid MIDI range"""
        self.pitch = max(0, min(127, self.pitch + semitones))
    
    def copy(self) -> 'MidiNote':
        """Create a deep copy of this note"""
        return MidiNote(
            pitch=self.pitch,
            start_time=self.start_time,
            end_time=self.end_time,
            velocity=self.velocity,
            channel=self.channel,
            selected=False  # Don't copy selection state
        )

@dataclass
class MidiEvent:
    """Represents non-note MIDI events (control changes, etc.)"""
    time: int                    # Absolute time in ticks
    event_type: EventType
    channel: int = 0            # 0-15
    data1: int = 0              # Controller number, program number, etc.
    data2: int = 0              # Value
    meta_data: Optional[bytes] = None  # For meta events
    
    def copy(self) -> 'MidiEvent':
        """Create a deep copy of this event"""
        return MidiEvent(
            time=self.time,
            event_type=self.event_type,
            channel=self.channel,
            data1=self.data1,
            data2=self.data2,
            meta_data=self.meta_data.copy() if self.meta_data else None
        )

class MidiTrack:
    """Represents a single MIDI track with notes and events"""
    
    def __init__(self, name: str = "Untitled Track", channel: int = 0):
        self.name = name
        self.channel = channel
        self.notes: List[MidiNote] = []
        self.events: List[MidiEvent] = []
        self.muted = False
        self.solo = False
        self.volume = 100           # 0-127
        self.pan = 64              # 0-127 (64 = center)
        self.program = 0           # 0-127 (instrument)
        
        # For UI state
        self.visible = True
        self.color = "#4A90E2"     # Default track color
        
        # Keep notes sorted by start time for efficient operations
        self._notes_sorted = True
        self._events_sorted = True
    
    def add_note(self, note: MidiNote):
        """Add a note to the track"""
        note.channel = self.channel  # Ensure note matches track channel
        self.notes.append(note)
        self._notes_sorted = False
    
    def remove_note(self, note: MidiNote) -> bool:
        """Remove a note from the track. Returns True if found and removed."""
        try:
            self.notes.remove(note)
            return True
        except ValueError:
            return False
    
    def add_event(self, event: MidiEvent):
        """Add an event to the track"""
        event.channel = self.channel  # Ensure event matches track channel
        self.events.append(event)
        self._events_sorted = False
    
    def _ensure_notes_sorted(self):
        """Ensure notes are sorted by start time"""
        if not self._notes_sorted:
            self.notes.sort(key=lambda n: n.start_time)
            self._notes_sorted = True
    
    def _ensure_events_sorted(self):
        """Ensure events are sorted by time"""
        if not self._events_sorted:
            self.events.sort(key=lambda e: e.time)
            self._events_sorted = True
    
    def get_notes_at_time(self, time: int) -> List[MidiNote]:
        """Get all notes playing at the specified time"""
        return [note for note in self.notes if note.contains_time(time)]
    
    def get_notes_in_range(self, start_time: int, end_time: int) -> List[MidiNote]:
        """Get all notes that overlap with the specified time range"""
        self._ensure_notes_sorted()
        result = []
        for note in self.notes:
            if note.start_time >= end_time:
                break  # Notes are sorted, so we can stop here
            if note.end_time > start_time:
                result.append(note)
        return result
    
    def get_notes_in_pitch_range(self, low_pitch: int, high_pitch: int) -> List[MidiNote]:
        """Get all notes within the specified pitch range (inclusive)"""
        return [note for note in self.notes if low_pitch <= note.pitch <= high_pitch]
    
    def quantize_notes(self, grid_size: int, strength: float = 1.0):
        """Quantize note start times to grid. Strength 0.0-1.0"""
        for note in self.notes:
            grid_time = round(note.start_time / grid_size) * grid_size
            note.start_time = int(note.start_time + (grid_time - note.start_time) * strength)
        self._notes_sorted = False
    
    def transpose_notes(self, semitones: int, selected_only: bool = False):
        """Transpose all notes (or just selected ones) by semitones"""
        for note in self.notes:
            if not selected_only or note.selected:
                note.transpose(semitones)
    
    def get_selected_notes(self) -> List[MidiNote]:
        """Get all currently selected notes"""
        return [note for note in self.notes if note.selected]
    
    def select_all_notes(self):
        """Select all notes in the track"""
        for note in self.notes:
            note.selected = True
    
    def clear_selection(self):
        """Clear selection from all notes"""
        for note in self.notes:
            note.selected = False
    
    def get_time_bounds(self) -> Tuple[int, int]:
        """Get the start and end times of all content in the track"""
        if not self.notes and not self.events:
            return (0, 0)
        
        min_time = float('inf')
        max_time = 0
        
        for note in self.notes:
            min_time = min(min_time, note.start_time)
            max_time = max(max_time, note.end_time)
        
        for event in self.events:
            min_time = min(min_time, event.time)
            max_time = max(max_time, event.time)
        
        return (int(min_time) if min_time != float('inf') else 0, int(max_time))
    
    def copy(self) -> 'MidiTrack':
        """Create a deep copy of this track"""
        new_track = MidiTrack(name=f"{self.name} Copy", channel=self.channel)
        new_track.notes = [note.copy() for note in self.notes]
        new_track.events = [event.copy() for event in self.events]
        new_track.muted = self.muted
        new_track.solo = self.solo
        new_track.volume = self.volume
        new_track.pan = self.pan
        new_track.program = self.program
        new_track.visible = self.visible
        new_track.color = self.color
        return new_track

class MidiDocument:
    """Main document class containing all MIDI data"""
    
    def __init__(self):
        self.tracks: List[MidiTrack] = []
        self.ticks_per_beat = 480
        self.tempo_bpm = 120
        self.time_signature = (4, 4)  # (numerator, denominator)
        self.key_signature = (0, True)  # (sharps/flats, is_major)
        
        # Document state
        self.filename = "Untitled.mid"
        self.modified = False
        
        # Timeline state for UI
        self.current_position = 0    # Current playback/edit position in ticks
        self.loop_start = 0
        self.loop_end = 0
        self.loop_enabled = False
        
        # Selection and editing state
        self.selected_tracks: Set[int] = set()  # Track indices
        self.clipboard: List[MidiNote] = []
    
    def add_track(self, track: Optional[MidiTrack] = None) -> MidiTrack:
        """Add a new track to the document"""
        if track is None:
            track = MidiTrack(name=f"Track {len(self.tracks) + 1}", channel=len(self.tracks) % 16)
        self.tracks.append(track)
        self.modified = True
        return track
    
    def remove_track(self, track_index: int) -> bool:
        """Remove a track by index. Returns True if successful."""
        if 0 <= track_index < len(self.tracks):
            del self.tracks[track_index]
            # Update selected tracks
            self.selected_tracks.discard(track_index)
            self.selected_tracks = {i - 1 if i > track_index else i for i in self.selected_tracks if i != track_index}
            self.modified = True
            return True
        return False
    
    def get_all_notes_at_time(self, time: int) -> List[Tuple[MidiNote, int]]:
        """Get all notes playing at time across all tracks. Returns (note, track_index) tuples."""
        result = []
        for track_idx, track in enumerate(self.tracks):
            if not track.muted:
                notes = track.get_notes_at_time(time)
                result.extend([(note, track_idx) for note in notes])
        return result
    
    def get_chord_at_time(self, time: int) -> List[int]:
        """Get all pitches playing at the specified time (for harmony analysis)"""
        notes_and_tracks = self.get_all_notes_at_time(time)
        return [note.pitch for note, _ in notes_and_tracks]
    
    def get_time_bounds(self) -> Tuple[int, int]:
        """Get the overall start and end times of the document"""
        if not self.tracks:
            return (0, 0)
        
        min_time = float('inf')
        max_time = 0
        
        for track in self.tracks:
            track_start, track_end = track.get_time_bounds()
            min_time = min(min_time, track_start)
            max_time = max(max_time, track_end)
        
        return (int(min_time) if min_time != float('inf') else 0, int(max_time))
    
    def ticks_to_beats(self, ticks: int) -> float:
        """Convert ticks to beats"""
        return ticks / self.ticks_per_beat
    
    def beats_to_ticks(self, beats: float) -> int:
        """Convert beats to ticks"""
        return int(beats * self.ticks_per_beat)
    
    def ticks_to_seconds(self, ticks: int) -> float:
        """Convert ticks to seconds at current tempo"""
        beats = self.ticks_to_beats(ticks)
        return (beats / self.tempo_bpm) * 60.0
    
    def seconds_to_ticks(self, seconds: float) -> int:
        """Convert seconds to ticks at current tempo"""
        beats = (seconds / 60.0) * self.tempo_bpm
        return self.beats_to_ticks(beats)
    
    def quantize_all_tracks(self, grid_size: int, strength: float = 1.0, selected_only: bool = False):
        """Quantize all tracks to grid"""
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
    
    def paste_notes_at_time(self, time: int, track_index: Optional[int] = None):
        """Paste clipboard notes at the specified time"""
        if not self.clipboard or not self.tracks:
            return
        
        # Use first track if no track specified
        if track_index is None:
            track_index = 0
        
        if track_index >= len(self.tracks):
            return
        
        target_track = self.tracks[track_index]
        
        # Find the earliest start time in clipboard
        earliest_time = min(note.start_time for note in self.clipboard)
        time_offset = time - earliest_time
        
        # Add offset notes to target track
        for note in self.clipboard:
            new_note = note.copy()
            new_note.start_time += time_offset
            new_note.end_time += time_offset
            target_track.add_note(new_note)
        
        self.modified = True
    
    @classmethod
    def from_midi_file(cls, filename: str) -> 'MidiDocument':
        """Create MidiDocument from a MIDI file"""
        doc = cls()
        doc.filename = filename
        
        try:
            mid = mido.MidiFile(filename)
            doc.ticks_per_beat = mid.ticks_per_beat
            
            for track_idx, mido_track in enumerate(mid.tracks):
                track = MidiTrack(name=f"Track {track_idx + 1}", channel=track_idx % 16)
                
                # Convert mido messages to our internal format
                current_time = 0
                active_notes = {}  # note -> (start_time, velocity)
                
                for msg in mido_track:
                    current_time += msg.time
                    
                    if msg.type == 'note_on' and msg.velocity > 0:
                        active_notes[msg.note] = (current_time, msg.velocity)
                    
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        if msg.note in active_notes:
                            start_time, velocity = active_notes[msg.note]
                            note = MidiNote(
                                pitch=msg.note,
                                start_time=start_time,
                                end_time=current_time,
                                velocity=velocity,
                                channel=msg.channel
                            )
                            track.add_note(note)
                            del active_notes[msg.note]
                    
                    elif msg.type == 'control_change':
                        event = MidiEvent(
                            time=current_time,
                            event_type=EventType.CONTROL_CHANGE,
                            channel=msg.channel,
                            data1=msg.control,
                            data2=msg.value
                        )
                        track.add_event(event)
                    
                    elif msg.type == 'program_change':
                        event = MidiEvent(
                            time=current_time,
                            event_type=EventType.PROGRAM_CHANGE,
                            channel=msg.channel,
                            data1=msg.program
                        )
                        track.add_event(event)
                        track.program = msg.program
                    
                    elif msg.type == 'set_tempo':
                        doc.tempo_bpm = int(60_000_000 / msg.tempo)
                        event = MidiEvent(
                            time=current_time,
                            event_type=EventType.TEMPO,
                            data1=msg.tempo
                        )
                        track.add_event(event)
                
                # Handle any notes that were never turned off
                for note, (start_time, velocity) in active_notes.items():
                    midi_note = MidiNote(
                        pitch=note,
                        start_time=start_time,
                        end_time=current_time,  # End at track end
                        velocity=velocity,
                        channel=track.channel
                    )
                    track.add_note(midi_note)
                
                doc.add_track(track)
            
            doc.modified = False
            return doc
            
        except Exception as e:
            print(f"Error loading MIDI file {filename}: {e}")
            return doc  # Return empty document
    
    def to_midi_file(self, filename: Optional[str] = None) -> bool:
        """Save document as MIDI file"""
        if filename is None:
            filename = self.filename
        
        try:
            mid = mido.MidiFile(ticks_per_beat=self.ticks_per_beat)
            
            for track in self.tracks:
                mido_track = mido.MidiTrack()
                mido_track.name = track.name
                
                # Collect all events (notes + control events)
                all_events = []
                
                # Add notes as note_on/note_off pairs
                for note in track.notes:
                    all_events.append((note.start_time, 'note_on', note.pitch, note.velocity, note.channel))
                    all_events.append((note.end_time, 'note_off', note.pitch, 0, note.channel))
                
                # Add control events
                for event in track.events:
                    all_events.append((event.time, event.event_type.value, event.data1, event.data2, event.channel))
                
                # Sort by time
                all_events.sort()
                
                # Convert to mido messages with delta times
                last_time = 0
                for time, event_type, data1, data2, channel in all_events:
                    delta_time = time - last_time
                    
                    if event_type == 'note_on':
                        msg = mido.Message('note_on', channel=channel, note=data1, velocity=data2, time=delta_time)
                    elif event_type == 'note_off':
                        msg = mido.Message('note_off', channel=channel, note=data1, velocity=data2, time=delta_time)
                    elif event_type == 'control_change':
                        msg = mido.Message('control_change', channel=channel, control=data1, value=data2, time=delta_time)
                    elif event_type == 'program_change':
                        msg = mido.Message('program_change', channel=channel, program=data1, time=delta_time)
                    else:
                        continue  # Skip unknown event types
                    
                    mido_track.append(msg)
                    last_time = time
                
                mid.tracks.append(mido_track)
            
            mid.save(filename)
            self.filename = filename
            self.modified = False
            return True
            
        except Exception as e:
            print(f"Error saving MIDI file {filename}: {e}")
            return False