# This is an old pre-existing file, it
# currently exports midi, we just need the not that
# may need to be refactored using imports, and etc

# This feature is used to combine multiple
# MIDI files, and/or single MIDI files with multiple tracks
# into one single MIDI file with only one track
# eliminating any duplicate notes


#!/usr/bin/env python3
import os
import sys

def main():
    """Main function with basic error checking first"""
    try:
        print("Starting MIDI File Combiner...")
        
        # Test basic imports first
        import tkinter as tk
        from tkinter import filedialog, messagebox, simpledialog
        print("Tkinter imported successfully")
        
        import mido
        from mido import MidiFile, MidiTrack
        print("Mido imported successfully")
        
        # Now run the actual program
        run_midi_combiner()
        
    except ImportError as e:
        print(f"Import Error: {e}")
        if "mido" in str(e):
            print("Please install mido: pip install mido")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(f"Error type: {type(e).__name__}")
        input("Press Enter to exit...")

def select_midi_files():
    """Select multiple MIDI files"""
    import tkinter as tk
    from tkinter import filedialog, messagebox
    
    root = tk.Tk()
    root.withdraw()
    
    # Show instructions
    messagebox.showinfo(
        "Select MIDI Files",
        "Select multiple MIDI files:\n\n"
        "• Hold Ctrl + click for individual files\n"
        "• Hold Shift + click for range selection\n"
        "• Ctrl+A to select all files"
    )
    
    file_paths = filedialog.askopenfilenames(
        title="Select MIDI files to combine",
        filetypes=[
            ("midi files", "*.mid"),
            ("midi files", "*.midi"),
            ("All files", "*.*")
        ]
    )
    
    root.destroy()
    return list(file_paths)

def get_output_filename():
    """Get output filename from user"""
    import tkinter as tk
    from tkinter import simpledialog
    
    root = tk.Tk()
    root.withdraw()
    
    filename = simpledialog.askstring(
        "Output Filename",
        "Enter name for combined MIDI file:",
        initialvalue="combined"
    )
    
    root.destroy()
    
    if filename:
        if not filename.endswith('.mid'):
            filename += '.mid'
        return filename
    return "combined.mid"

def combine_midi_files(file_paths, output_path):
    """Combine MIDI files into a single unified track"""
    import mido
    
    if not file_paths:
        print("No files to combine")
        return False
    
    try:
        print("Creating single unified MIDI track...")
        
        # Collect all messages from all files
        all_messages = []
        ticks_per_beat = 480  # Default value
        
        for i, file_path in enumerate(file_paths):
            print(f"Processing {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")
            
            try:
                mid = mido.MidiFile(file_path)
                
                # Use first file's timing
                if i == 0:
                    ticks_per_beat = mid.ticks_per_beat
                
                # Convert all tracks to absolute time and collect messages
                for track in mid.tracks:
                    absolute_time = 0
                    for msg in track:
                        absolute_time += msg.time
                        # Only include note and control messages, skip meta messages
                        if not msg.is_meta:
                            # Create new message with absolute time
                            new_msg = msg.copy()
                            new_msg.time = absolute_time
                            all_messages.append(new_msg)
                            
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        if not all_messages:
            print("No MIDI messages found in any file")
            return False
        
        # Sort all messages by absolute time
        print("Sorting messages by time...")
        all_messages.sort(key=lambda msg: msg.time)
        
        # Create single track with relative timing
        print("Creating unified track...")
        unified_track = mido.MidiTrack()
        last_time = 0
        
        for msg in all_messages:
            # Convert back to relative time
            msg.time = msg.time - last_time
            last_time += msg.time
            unified_track.append(msg)
        
        # Create the final MIDI file with single track
        combined_mid = mido.MidiFile()
        combined_mid.ticks_per_beat = ticks_per_beat
        combined_mid.type = 0  # Type 0 = single track
        combined_mid.tracks.append(unified_track)
        
        # Save file
        print(f"Saving unified MIDI to: {output_path}")
        combined_mid.save(output_path)
        
        print(f"Successfully combined {len(file_paths)} files into single track")
        print(f"Total messages: {len(all_messages)}")
        return True
        
    except Exception as e:
        print(f"Error combining files: {e}")
        return False

def show_success_message(output_filename, num_files):
    """Show success dialog"""
    import tkinter as tk
    from tkinter import messagebox
    
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Success!",
            f"Combined {num_files} MIDI files successfully!\n\n"
            f"Output: {output_filename}"
        )
        root.destroy()
    except:
        print("Success dialog failed, but file was created successfully")

def show_error_message():
    """Show error dialog"""
    import tkinter as tk
    from tkinter import messagebox
    
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error",
            "Failed to combine MIDI files.\nCheck console for details."
        )
        root.destroy()
    except:
        print("Error dialog failed")

def run_midi_combiner():
    """Main program logic"""
    print("\nMIDI File Combiner - Layered Mode")
    print("=" * 40)
    
    # Select files
    print("Opening file selection...")
    file_paths = select_midi_files()
    
    if not file_paths:
        print("No files selected")
        input("Press Enter to exit...")
        return
    
    print(f"\nSelected {len(file_paths)} files:")
    for i, path in enumerate(file_paths, 1):
        print(f"  {i}. {os.path.basename(path)}")
    
    # Get output name
    print("\nGetting output filename...")
    output_filename = get_output_filename()
    print(f"Output will be: {output_filename}")
    
    # Combine files
    print(f"\nCombining files...")
    success = combine_midi_files(file_paths, output_filename)
    
    # Show result
    if success:
        show_success_message(output_filename, len(file_paths))
        print("\n✓ Single unified MIDI track created successfully!")
    else:
        show_error_message()
        print("\n✗ Process failed")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()