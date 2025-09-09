# MIDI_COMPOSE

is a Python-based MIDI sequencing and editing application designed for comprehensive musical data manipulation. Its core component is an interactive piano roll, which provides users with granular control over note parameters.

**Core Functionality**

_Piano Roll Interface:_ The primary UI facilitates direct note editing, enabling users to independently modify pitch, timing, duration, and velocity. Notes can be added, deleted, or adjusted by their start and end points.

_Customizable Grid System:_ A visual grid aids in the precise placement of notes. This grid can be configured to standard, complex, odd, and mixed meters, including a comprehensive list of time signatures, without affecting MIDI playback.

_Velocity Editor:_ A dedicated, synchronized Velocity Editor provides fine-grained control over note dynamics. Bezeir curve type tools allow the user to make precise dynamic adjustments over time.  Want a mathematically precise 20 bar crescendo? You got it. Want a mathemtcially correct 
$y(t) = 20 \cdot \sin(\pi t)$ 
sine wave for your dynamics? You got it.

_VST Integration:_ The application supports real-time audio playback through Virtual Studio Technology (VST) instruments (e.g., Kontakt, Spitfire LABS). However, it does not support the import, export, or editing of audio files.

**Real-Time Processing Architecture**

The application uses a real-time, continuous processing model that moves away from traditional, menu-driven workflows. All features, including analysis, transformations, and generative functions, run in the background as dynamic filters that provide real-time suggestions and modifications to the MIDI data. This creates a WYSIWYG environment and a live feedback loop, giving users immediate visual feedback and allowing them to instantly decide whether to apply computational results to the score.

# MIDI_COMPOSE

 is distributed as a standalone Windows executable (.exe). The Python source code is compiled into C-level bytecode using Nuitka, which optimizes performance for a low-latency user experience.