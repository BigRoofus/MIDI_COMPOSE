# MIDI_COMPOSE

is a Python-based MIDI sequencing and editing application designed for comprehensive musical data manipulation. Its core component is an interactive piano roll, which provides users with granular control over note parameters.

**Core Functionality**

_Piano Roll Interface:_ The primary UI facilitates direct note editing, enabling users to independently modify pitch, timing, duration, and velocity. Notes can be added, deleted, or adjusted by their start and end points.

_Customizable Grid System:_ A visual grid aids in the precise placement of notes. This grid can be configured to standard, complex, odd, and mixed meters, including a comprehensive list of time signatures, without affecting MIDI playback.

_Velocity Editor:_ A dedicated, synchronized panel allows for fine-grained control of note velocity, offering a dynamic range of 1-127.

_VST Integration:_ The application supports real-time audio playback through Virtual Studio Technology (VST) instruments (e.g., Kontakt, Spitfire LABS). However, it does not support the import, export, or editing of audio files.

**Real-Time Processing Architecture**

The application operates on a continuous, real-time processing model, deviating from traditional menu-driven workflows. All features, including analysis, transformations, and generative functions, are active and computed in the background.

_Dynamic Filtering:_ These background processes serve as dynamic filters, providing real-time suggestions and modifications to the MIDI data. Users can toggle the visibility of these filters to preview their effects on the score.

_Live Feedback Loop:_ This approach creates a "What-You-See-Is-What-You-Get" (WYSIWYG) environment, where users receive instantaneous visual feedback on potential changes. The system functions as a live feedback loop, allowing for immediate decisions on incorporating or discarding computational results.

MIDI_COMPOSE is distributed as a standalone Windows executable (.exe). The Python source code is compiled into C-level bytecode using Nuitka, which optimizes performance for a low-latency user experience. The distribution does not require an installer and includes a custom application icon.