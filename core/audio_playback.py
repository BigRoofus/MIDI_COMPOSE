import pretty_midi
import mido
import time
import simpleaudio as sa

class MidiPlayback:
    def __init__(self, document_path: str):
        # Load the MIDI with pretty_midi
        self.midi = pretty_midi.PrettyMIDI(document_path)
        self.is_playing = False
        self.current_position = 0
        self.tempo = 120
        self.midi_data = None  # To store the synthesized audio

        # Try to open GS Wavetable
        try:
            self.outport = mido.open_output("Microsoft GS Wavetable Synth 0")
        except IOError:
            try:
                self.outport = mido.open_output()  # fallback: first available
            except IOError:
                self.outport = None # No output port available
        
        # Add code here to use the sounds provided by pretty_midi if nothing else works
        if self.outport is None:
            print("No MIDI output port available. Synthesizing audio with pretty_midi.")
            self.midi_data = self.midi.synthesize(fs=44100)
            
    def play(self):
        """Start playback"""
        if self.is_playing:
            return
        self.is_playing = True

        if self.outport:
            # Iterate through events with timing
            for instrument in self.midi.instruments:
                for note in instrument.notes:
                    if not self.is_playing:
                        break

                    # Note on
                    msg_on = mido.Message(
                        "note_on", note=note.pitch, velocity=note.velocity, channel=instrument.program % 16
                    )
                    self.outport.send(msg_on)

                    # Wait for note duration
                    time.sleep(note.end - note.start)

                    # Note off
                    msg_off = mido.Message(
                        "note_off", note=note.pitch, velocity=0, channel=instrument.program % 16
                    )
                    self.outport.send(msg_off)
        elif self.midi_data is not None:
            # Play the synthesized audio
            play_obj = sa.play_buffer(self.midi_data.astype('int16'), 1, 2, 44100)
            play_obj.wait_done()
            self.is_playing = False

    def stop(self):
        """Stop playback"""
        self.is_playing = False
        if self.outport:
            for ch in range(16):
                self.outport.send(mido.Message("control_change", channel=ch, control=123, value=0))

    def set_position(self, ticks: int):
        """Set playback position (not precise yet)"""
        self.current_position = ticks