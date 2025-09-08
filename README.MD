MIDI_COMPOSE is a pure MIDI sequencing and editing application written in Python. Its primary interface is a piano roll that facilitates comprehensive note manipulation, including adjusting pitch, timing, duration, and velocity.

Key Features:
Piano Roll: Allows for independent adjustment of note position (up/down and left/right) and duration (start/end points). Users can add or remove notes as needed.

Customizable Grid: A visual grid aids in note placement and can be set to common or complex time signatures without affecting MIDI data playback.

Velocity Editor: A dedicated panel synchronized with the piano roll provides precise control over note volume, with a range of 1-127.

VST Integration: The application can interface with VSTs (e.g., Kontakt, Spitfire LABS) for real-time audio playback during editing. It does not handle audio file import, export, or editing.

MIDI_COMPOSE is distributed as a standalone Windows executable (.exe) with a custom icon and no installer. The Python source code is compiled with Nuitka to achieve C-level performance.
