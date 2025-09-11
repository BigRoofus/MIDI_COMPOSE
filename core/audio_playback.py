import pretty_midi
import mido
import time

class MidiPlayback:
    def __init__(self, document_path: str):
        # Load the MIDI with pretty_midi
        self.midi = pretty_midi.PrettyMIDI(document_path)
        self.is_playing = False
        self.current_position = 0
        self.tempo = 120

        # Try to open GS Wavetable
        try:
            self.outport = mido.open_output("Microsoft GS Wavetable Synth 0")
        except IOError:
            self.outport = mido.open_output()  # fallback: first available

    def play(self):
        """Start playback"""
        if self.is_playing:
            return
        self.is_playing = True

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

    def stop(self):
        """Stop playback"""
        self.is_playing = False
        for ch in range(16):
            self.outport.send(mido.Message("control_change", channel=ch, control=123, value=0))

    def set_position(self, ticks: int):
        """Set playback position (not precise yet)"""
        self.current_position = ticks

# PrettyMIDI stores times in seconds, so you'd map ticks to seconds if needed
