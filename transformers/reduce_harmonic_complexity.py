# This is an old pre-exsting file
# It may need to be modified to be more modular
# (using imports and etc)

#!/usr/bin/env python3
"""
MIDI Voice Reducer
Reduces polyphonic MIDI files to a specified number of voices using dissonance-based note selection.
"""

import sys
import os
import subprocess
from collections import defaultdict

def install_package(package):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def check_and_install_dependencies():
    """Check for required packages and install them if missing."""
    required_packages = {
        'mido': 'mido',
        'tkinter': None  # tkinter is built-in, but we'll check it separately
    }
    
    print("🔍 Checking dependencies...")
    
    # Check mido
    try:
        import mido
        print("   ✅ mido - OK")
    except ImportError:
        print("   ❌ mido - Not found, installing...")
        if install_package('mido'):
            print("   ✅ mido - Installed successfully")
            import mido
        else:
            print("   ❌ Failed to install mido. Please install manually with: pip install mido")
            return False
    
    # Check tkinter
    try:
        import tkinter
        from tkinter import filedialog
        print("   ✅ tkinter - OK")
    except ImportError:
        print("   ❌ tkinter - Not available")
        print("      tkinter is usually included with Python, but seems to be missing.")
        print("      On Ubuntu/Debian: sudo apt-get install python3-tk")
        print("      On macOS: tkinter should be included with Python")
        print("      On Windows: tkinter should be included with Python")
        return False
    
    print("   🎉 All dependencies are ready!")
    return True

# Check dependencies before importing
if not check_and_install_dependencies():
    input("\nPress Enter to exit...")
    sys.exit(1)

# Now we can safely import
import mido
from tkinter import filedialog
import tkinter as tk

class MidiVoiceReducer:
    # Dissonance ranking from most to least dissonant (semitones from root)
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
    
    def __init__(self, input_file, output_file, max_voices, consonance_preference=0, key_analysis_window=6, min_key_duration=2):
        self.input_file = input_file
        self.output_file = output_file
        self.max_voices = max_voices
        self.consonance_preference = consonance_preference  # -10 to 10
        self.key_analysis_window = key_analysis_window  # How many measures to look back
        self.min_key_duration = min_key_duration  # Minimum measures for a stable key
        self.total_events = 0
        self.processed_events = 0
        self.current_key = None  # Will store (root, mode) tuple
        self.key_confidence = 0.0
        self.ticks_per_beat = 480  # Default, will be updated
        self.key_changes = []  # Track key changes with timing
        self.key_buffer = []  # Buffer to track recent key detections
        self.last_stable_key = None  # Last confirmed stable key
        
    def ticks_to_measure(self, ticks):
        """Convert ticks to measure number (approximate)."""
        # Assume 4/4 time signature for simplicity
        ticks_per_measure = self.ticks_per_beat * 4
        return int(ticks / ticks_per_measure) + 1
    
    def process_midi_file(self):
        """Process the MIDI file and reduce voices."""
        print(f"📁 Loading MIDI file: {self.input_file}")
        
        try:
            mid = mido.MidiFile(self.input_file)
        except Exception as e:
            print(f"❌ Error loading MIDI file: {e}")
            return False
        
        self.ticks_per_beat = mid.ticks_per_beat
        
        print(f"🎵 MIDI file loaded successfully")
        print(f"   Tracks: {len(mid.tracks)}")
        print(f"   Ticks per beat: {mid.ticks_per_beat}")
        print(f"   Type: {mid.type}")
        
        # Count total events for progress tracking
        self.total_events = sum(len(track) for track in mid.tracks)
        print(f"   Total events: {self.total_events}")
        print()
        
        print(f"🔄 Combining all tracks and reducing to {self.max_voices} voices...")
        
        # Step 1: Extract all note events from all tracks and combine them
        all_note_events = []
        meta_events = []  # Store meta events (tempo, time signature, etc.)
        current_time = 0
        
        for track_idx, track in enumerate(mid.tracks):
            print(f"   Reading track {track_idx + 1}/{len(mid.tracks)}: {track.name if hasattr(track, 'name') else 'Unnamed'}")
            
            current_time = 0
            for msg in track:
                current_time += msg.time
                self.processed_events += 1
                
                if self.processed_events % 100 == 0:
                    progress = (self.processed_events / self.total_events) * 50  # First 50% for reading
                    print(f"      Progress: {progress:.1f}%", end='\r')
                
                if msg.type in ['note_on', 'note_off']:
                    # Convert note_on with velocity 0 to note_off
                    if msg.type == 'note_on' and msg.velocity == 0:
                        msg_type = 'note_off'
                        velocity = 0
                    else:
                        msg_type = msg.type
                        velocity = msg.velocity
                    
                    all_note_events.append((current_time, msg_type, msg.note, velocity, msg.channel))
                elif msg.type in ['set_tempo', 'time_signature', 'key_signature', 'text', 'copyright', 'track_name', 'instrument_name', 'marker', 'cue_marker', 'program_change', 'control_change']:
                    # Store meta and control events for the first track only to avoid duplicates
                    if track_idx == 0 or msg.type in ['program_change', 'control_change']:
                        meta_events.append((current_time, msg.copy()))
        
        print("\n   Combining all notes from all tracks...")
        
        # Step 2: Apply voice reduction to combined note events
        reduced_events = self.reduce_voices_combined(all_note_events)
        
        # Step 3: Separate reduced events into voice tracks
        voice_tracks_events = self.separate_into_voices(reduced_events)
        
        print(f"   Creating {self.max_voices} voice tracks...")
        
        # Step 4: Create new MIDI file with voice tracks
        new_mid = mido.MidiFile(type=1, ticks_per_beat=mid.ticks_per_beat)  # Type 1 for multiple tracks
        
        # Create meta track (track 0) with tempo, time signature, etc.
        meta_track = mido.MidiTrack()
        meta_track.name = 'Meta Track'
        
        # Add meta events with proper timing
        meta_events.sort(key=lambda x: x[0])
        last_time = 0
        for time, msg in meta_events:
            delta_time = time - last_time
            msg.time = delta_time
            meta_track.append(msg)
            last_time = time
        
        new_mid.tracks.append(meta_track)
        
        # Create voice tracks
        for voice_num in range(self.max_voices):
            voice_track = mido.MidiTrack()
            voice_track.name = f'Voice {voice_num + 1}'
            
            # Add program change for piano (optional)
            voice_track.append(mido.Message('program_change', channel=voice_num, program=0, time=0))
            
            # Add voice events
            events = voice_tracks_events.get(voice_num, [])
            events.sort(key=lambda x: x[0])
            
            last_time = 0
            for time, msg_type, note, velocity, original_channel in events:
                delta_time = time - last_time
                
                if msg_type == 'note_on' and velocity > 0:
                    msg = mido.Message('note_on', channel=voice_num, note=note, velocity=velocity, time=delta_time)
                else:
                    msg = mido.Message('note_off', channel=voice_num, note=note, velocity=0, time=delta_time)
                
                voice_track.append(msg)
                last_time = time
            
            new_mid.tracks.append(voice_track)
        
        # Print key analysis results
        self.print_key_analysis()
        
        print(f"💾 Saving reduced MIDI file: {self.output_file}")
        
        try:
            new_mid.save(self.output_file)
            print(f"✅ Successfully created {self.output_file}")
            print(f"   Original: {len(mid.tracks)} tracks")
            print(f"   Reduced: 1 meta track + {self.max_voices} voice tracks")
            print(f"   Voice reduction applied to combined polyphony")
            return True
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return False
    
    def print_key_analysis(self):
        """Print the key analysis results by measure."""
        if not self.key_changes:
            print("\n🎼 Key Analysis: No key changes detected")
            return
        
        print(f"\n🎼 Key Analysis:")
        
        # Group consecutive measures with the same key
        current_key = None
        start_measure = 1
        
        for i, (measure, key_info) in enumerate(self.key_changes):
            if key_info != current_key:
                # Print the previous key range if we have one
                if current_key is not None:
                    end_measure = measure - 1 if measure > start_measure else start_measure
                    if start_measure == end_measure:
                        measure_text = f"mm. {start_measure}"
                    else:
                        measure_text = f"mm. {start_measure} - {end_measure}"
                    
                    if current_key is None:
                        print(f"   {measure_text}: Atonal")
                    else:
                        key_name = self.get_key_name(current_key[0], current_key[1])
                        print(f"   {measure_text}: {key_name}")
                
                # Start new key section
                current_key = key_info
                start_measure = measure
        
        # Print the final key section
        if current_key is not None or self.key_changes:
            last_measure = self.key_changes[-1][0] if self.key_changes else 1
            if start_measure == last_measure:
                measure_text = f"mm. {start_measure}"
            else:
                measure_text = f"mm. {start_measure} - {last_measure}+"
            
            if current_key is None:
                print(f"   {measure_text}: Atonal")
            else:
                key_name = self.get_key_name(current_key[0], current_key[1])
                print(f"   {measure_text}: {key_name}")
    
    def reduce_voices_combined(self, note_events):
        """Apply voice reduction to combined note events from all tracks."""
        print("   Applying dissonance-based voice reduction...")
        
        # Group events by time to find simultaneous notes
        events_by_time = defaultdict(list)
        for event in note_events:
            time = event[0]
            events_by_time[time].append(event)
        
        # Track active notes across all original tracks
        active_notes = {}  # note -> (start_time, velocity, channel)
        reduced_events = []
        processed_times = 0
        total_times = len(events_by_time)
        
        for time in sorted(events_by_time.keys()):
            processed_times += 1
            if processed_times % 10 == 0:
                progress = 50 + (processed_times / total_times) * 50  # Second 50% for processing
                print(f"      Progress: {progress:.1f}%", end='\r')
            
            events = events_by_time[time]
            
            # Process note offs first
            notes_to_turn_off = []
            for event in events:
                if event[1] == 'note_off':
                    note = event[2]
                    if note in active_notes:
                        notes_to_turn_off.append(event)
                        del active_notes[note]
            
            # Add note offs to reduced events
            reduced_events.extend(notes_to_turn_off)
            
            # Collect new note ons
            new_note_ons = []
            for event in events:
                if event[1] == 'note_on' and event[3] > 0:
                    new_note_ons.append(event)
            
            if new_note_ons:
                # Get all currently playing notes plus new ones
                all_current_notes = list(active_notes.keys()) + [e[2] for e in new_note_ons]
                
                # Apply voice reduction to the combined polyphony
                selected_notes = self.select_notes_by_dissonance(all_current_notes)
                
                # Track key changes by measure with stability checking
                current_measure = self.ticks_to_measure(time)
                current_key_info = self.current_key if self.key_confidence > 0.65 else None
                
                # Update key analysis with stability checking
                self.update_key_analysis(current_measure, current_key_info)
                
                # Turn off notes that are no longer selected
                notes_to_stop = []
                for note in list(active_notes.keys()):
                    if note not in selected_notes:
                        # Create note off event
                        start_time, velocity, channel = active_notes[note]
                        notes_to_stop.append((time, 'note_off', note, 0, channel))
                        del active_notes[note]
                
                reduced_events.extend(notes_to_stop)
                
                # Turn on only selected new notes
                for event in new_note_ons:
                    note = event[2]
                    if note in selected_notes:
                        reduced_events.append(event)
                        active_notes[note] = (time, event[3], event[4])
        
        print(f"\n   Voice reduction complete: {len(reduced_events)} events")
        return reduced_events
    
    def separate_into_voices(self, reduced_events):
        """Separate reduced events into individual voice tracks."""
        print("   Distributing notes to voice tracks...")
        
        # Sort events by time
        reduced_events.sort(key=lambda x: x[0])
        
        # Track which voice each note is assigned to
        note_to_voice = {}
        voice_tracks = {i: [] for i in range(self.max_voices)}
        active_voices = [None] * self.max_voices  # Track what note each voice is playing
        
        # Group events by time for simultaneous processing
        events_by_time = defaultdict(list)
        for event in reduced_events:
            time = event[0]
            events_by_time[time].append(event)
        
        for time in sorted(events_by_time.keys()):
            events = events_by_time[time]
            
            # Process note offs first
            for event in events:
                if event[1] == 'note_off':
                    note = event[2]
                    if note in note_to_voice:
                        voice_num = note_to_voice[note]
                        voice_tracks[voice_num].append(event)
                        active_voices[voice_num] = None
                        del note_to_voice[note]
            
            # Process note ons - assign to voices by pitch (highest to lowest)
            note_ons = [e for e in events if e[1] == 'note_on' and e[3] > 0]
            note_ons.sort(key=lambda x: x[2], reverse=True)  # Sort by pitch, highest first
            
            for event in note_ons:
                note = event[2]
                
                # Find an available voice or reassign based on pitch
                assigned_voice = None
                
                # First, try to find a completely free voice
                for i in range(self.max_voices):
                    if active_voices[i] is None:
                        assigned_voice = i
                        break
                
                # If no free voice, assign based on pitch range preference
                if assigned_voice is None:
                    # Assign higher notes to lower-numbered voices (treble first)
                    for i in range(self.max_voices):
                        if active_voices[i] is not None:
                            current_note = active_voices[i]
                            # Replace if this note is higher (for treble voices) or lower (for bass voices)
                            if (i < self.max_voices // 2 and note > current_note) or \
                               (i >= self.max_voices // 2 and note < current_note):
                                # Turn off the current note in this voice
                                old_note = active_voices[i]
                                voice_tracks[i].append((time, 'note_off', old_note, 0, event[4]))
                                if old_note in note_to_voice:
                                    del note_to_voice[old_note]
                                assigned_voice = i
                                break
                    
                    # If still no assignment, use the first voice
                    if assigned_voice is None:
                        assigned_voice = 0
                        if active_voices[0] is not None:
                            old_note = active_voices[0]
                            voice_tracks[0].append((time, 'note_off', old_note, 0, event[4]))
                            if old_note in note_to_voice:
                                del note_to_voice[old_note]
                
                # Assign the note to the selected voice
                voice_tracks[assigned_voice].append(event)
                note_to_voice[note] = assigned_voice
                active_voices[assigned_voice] = note
        
        return voice_tracks

def select_midi_file():
    """Open a file picker to select a single MIDI file."""
    # Create a root window and hide it
    root = tk.Tk()
    root.withdraw()
    
    print("📁 Opening file picker...")
    
    # Open file dialog for single file
    file_path = filedialog.askopenfilename(
        title="Select MIDI file",
        filetypes=[
            ("midi files", "*.mid *.midi"),
            ("All files", "*.*")
        ],
        initialdir=os.getcwd()
    )
    
    root.destroy()
    
    if file_path:
        return file_path
    else:
        print("   No file selected.")
        return None

def select_midi_files():
    """Open a file picker to select multiple MIDI files."""
    # Create a root window and hide it
    root = tk.Tk()
    root.withdraw()
    
    print("📁 Opening file picker...")
    
    # Open file dialog for multiple files
    file_paths = filedialog.askopenfilenames(
        title="Select MIDI files",
        filetypes=[
            ("midi files", "*.mid *.midi"),
            ("All files", "*.*")
        ],
        initialdir=os.getcwd()
    )
    
    root.destroy()
    
    if file_paths:
        return list(file_paths)
    else:
        print("   No files selected.")
        return []

def main():
    print("🎼 MIDI Voice Reducer")
    print("=" * 50)
    print()
    
    # Use file picker to select MIDI file
    input_file = select_midi_file()
    
    if not input_file:
        print("❌ No file selected. Exiting...")
        input("\nPress Enter to exit...")
        return 1
    
    print(f"\n✅ Selected: {os.path.basename(input_file)}")
    
    # Get number of voices
    while True:
        try:
            voices_input = input("\nHow many voices do you want? (e.g., 4 for 4-part harmony): ").strip()
            max_voices = int(voices_input)
            if max_voices < 1:
                print("Number of voices must be at least 1")
                continue
            elif max_voices > 20:
                print("That's a lot of voices! Are you sure? (y/n): ", end="")
                confirm = input().strip().lower()
                if confirm not in ['y', 'yes']:
                    continue
            break
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            return 1
    
    # Get consonance/dissonance preference
    while True:
        try:
            print("\nConsonance/Dissonance Preference:")
            print("  -10 = Most dissonant (keep clashing notes)")
            print("   0  = Neutral (original algorithm)")
            print("  +10 = Most consonant (keep harmonic notes)")
            
            pref_input = input("\nEnter preference (-10 to 10): ").strip()
            consonance_pref = int(pref_input)
            if consonance_pref < -10 or consonance_pref > 10:
                print("Please enter a number between -10 and 10")
                continue
            break
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            return 1
    
    # Get key analysis parameters
    while True:
        try:
            print("\nKey Analysis Settings:")
            print("  Analysis window = how many measures to look back for key detection")
            print("  Minimum duration = how many measures a key must persist to be reported")
            
            window_input = input(f"\nAnalysis window in measures (default 3): ").strip()
            if window_input == "":
                key_window = 3
            else:
                key_window = int(window_input)
                if key_window < 2 or key_window > 32:
                    print("Please enter a number between 2 and 32")
                    continue
            
            duration_input = input(f"Minimum measures for key detection (default 2): ").strip()
            if duration_input == "":
                min_duration = 2
            else:
                min_duration = int(duration_input)
                if min_duration < 1 or min_duration > key_window:
                    print(f"Please enter a number between 1 and {key_window}")
                    continue
            break
        except ValueError:
            print("Please enter valid numbers")
        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            return 1
    
    # Generate output filename
    base, ext = os.path.splitext(input_file)
    pref_suffix = f"_d{abs(consonance_pref)}" if consonance_pref < 0 else f"_c{consonance_pref}" if consonance_pref > 0 else ""
    output_file = f"{base}_reduced_{max_voices}voice{pref_suffix}{ext}"
    
    print(f"\n📋 Dissonance Priority (Most to Least Dissonant):")
    for i, (semitones, name) in enumerate(MidiVoiceReducer.DISSONANCE_RANKING.items(), 1):
        print(f"   {i:2}. {name} ({semitones} semitones)")
    
    print(f"\n⚙️ Processing Settings:")
    print(f"   Input: {os.path.basename(input_file)}")
    print(f"   Output: {os.path.basename(output_file)}")
    print(f"   Max voices: {max_voices}")
    if consonance_pref < 0:
        print(f"   Preference: Dissonant ({consonance_pref})")
    elif consonance_pref > 0:
        print(f"   Preference: Consonant (+{consonance_pref})")
    else:
        print(f"   Preference: Neutral (0)")
    print(f"   Key analysis window: {key_window} measures")
    print(f"   Minimum key duration: {min_duration} measures")
    print()
    
    # Process the file
    reducer = MidiVoiceReducer(input_file, output_file, max_voices, consonance_pref, key_window, min_duration)
    success = reducer.process_midi_file()
    
    print()
    if success:
        print("🎉 Voice reduction completed successfully!")
        print(f"   Your reduced MIDI file: {os.path.basename(output_file)}")
        input("\nPress Enter to exit...")
        return 0
    else:
        print("❌ Voice reduction failed.")
        input("\nPress Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())