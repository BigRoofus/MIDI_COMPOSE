mico, pronounced "mee-ko," short for MIDI_COMPOSE, 
is a MIDI sequencing and editing application designed for comprehensive musical data manipulation.
<br>
<br>

**Standard Piano Roll Interface**

The primary UI facilitates the same standard piano roll note editing found in most modern notation software. Enabling independent modification of pitch, timing, duration, and velocity. Notes can be added, deleted, elongated or shortened. Any user familiar with a piano roll editor will be instantly at home.
<br>
<br>

**Real-Time Processing Architecture**

mico uses a real-time, continuous processing model that moves away from traditional, menu-driven workflows. All features, including analysis, transformations, and generative functions, run in the background as dynamic filters that provide real-time suggestions and modifications to the MIDI data. This creates a WYSIWYG environment with immediate visual and sonic feedback, allowing users to decide whether or not to apply computational suggestions non-destructively and in real-time.
<br>
<br>

**Advanced Velocity Editor**

The Advanced Velocity Editor enables unprecedented command over a composition's dynamics. More than just offering fine-grained control over individual note dynamics, tools like the Dynamics Curve Tool (for three-point cubic Bezier curves), the Freehand Draw Tool (for freely drawing dynamic curves by hand), the Mathematical Formula Input Tool (for equation based shaping), and the Classic Shapes Tool (triangle, oval, polygon, invert shape, and more); give complete command over any selection of notes' dynamic landscape. Want a mathematically precise 20-bar crescendo, the tools provide it. Want a mathematically correct
$y(t) = 20 \cdot \sin(\pi t)$
sine wave, the tools provide it. 
<br>
<br>

**Advanced Grid System**

The Advanced Grid is a visual tool for precise note placement, switchable to any time signature or meter, standard, complex, odd, or mixed, at any BPM, while never altering the MIDI data’s original time signatures.
<br>
<br>

**pip CLI install command**

pip install PyQt6 numpy pretty_midi mido scipy matplotlib dataclasses-json simpleaudio