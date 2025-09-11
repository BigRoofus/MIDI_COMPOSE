class MidiPlayback:
    def __init__(self, document: MidiDocument):
        self.document = document
        self.is_playing = False
        self.current_position = 0
        self.tempo = 120
    
    def play(self):
        """Start playback"""
        pass
    
    def stop(self):
        """Stop playback"""
        pass
    
    def set_position(self, ticks: int):
        """Set playback position"""
        pass
