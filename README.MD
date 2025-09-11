mico, pronounced "mee-ko," short for MIDI_COMPOSE, is a MIDI sequencing and editing application designed for comprehensive musical data manipulation.
<br>
<br>

**Real-Time Processing Architecture**

mico uses a real-time, continuous processing model that moves away from traditional, menu-driven workflows. All features, including analysis, transformations, and generative functions, run in the background as dynamic filters that provide real-time suggestions and modifications to the MIDI data. This creates a WYSIWYG environment and a live feedback loop, giving the user immediate visual and sonic feedback and allowing them to instantly decide whether to apply computational results to the score.
<br>
<br>

**Advanced Velocity Editor**

The Advanced Velocity Editor gives the user unprecedented command over a composition's dynamics. More than just offering fine-grained control over individual note dynamics, tools like the Dynamics Curve Tool (for three-point cubic Bezier curves), the Freehand Draw Tool (for freely drawing dynamic curves), the Mathematical Formula Input Tool (for equation-based shaping), and the Classic Shapes Tool (triangle, oval, polygon, invert shape, and more) give the user complete command of the music's dynamic landscape. If the user wants a mathematically precise 20-bar crescendo, the tools provide it. If the user wants a mathematically correct
$y(t) = 20 \cdot \sin(\pi t)$
sine wave, the tools provide it. 
<br>
<br>

**Advanced Grid System**

The Advanced Grid is a visual tool for precise note placement, adaptable to any time signature, standard, complex, odd, or mixed, and any BPM, while never altering the MIDI file’s original time signatures.
<br>
<br>

**Standard Piano Roll Interface**

The primary UI facilitates the same standard piano roll note editing as most modern DAWs, enabling the user to independently modify pitch, timing, duration, and velocity. Notes can be added, deleted, or adjusted by their start and end points. Any user familiar with a piano roll editor will be instantly at home.
<br>
<br>

**pip install**

pip install PyQt6 numpy pretty_midi mido scipy matplotlib dataclasses-json simpleaudio