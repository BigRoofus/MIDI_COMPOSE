<img src="logo.png" alt="A beautiful sunset" width="450" height="275">

mico, pronounced "mee-ko," short for MIDI_COMPOSE, is a MIDI sequencing and editing application designed for comprehensive musical data manipulation.
<br><br><br>

**Real-Time Processing Architecture**

mico uses a real-time, continuous processing model that moves away from traditional, menu-driven workflows. All features, including analysis, transformations, and generative functions, run in the background as dynamic filters that provide real-time suggestions and modifications to the MIDI data. This creates a WYSIWYG environment and a live feedback loop, giving users immediate visual feedback and allowing them to instantly decide whether to apply computational results to the score.
<br>
<br>

**MusicDNA**

MusicDNA is a radical new approach to analyzing and creating musical compositions. More than just an analysis tool, MusicDNA is a blueprint and a data format. During analysis, MusicDNA performs a bar-by-bar sliding analysis of MIDI data, resulting in a detailed blueprint that provides a clear and concise understanding of the music's construction. It goes beyond a simple note list to identify the building blocks of a composition based on pitch set changes and a Jaccard similarity metric. The analysis also pinpoints the main motif and calculates note density, offering a concise, data-driven summary that's perfect for composers, analysts, and anyone looking to deconstruct music at a fundamental level. This blueprint can then be saved as an external file (.musdna extension, in JSON format) and reused later as a transform.
<br>
<br>

**Advanced Velocity Editor** 

A completely new and revolutionary Velocity Editor gives you more than just fine-grained control over individual note dynamics. The Advanced Velocity Editor provides a much more imaginative and comprehensive approach. With tools like the Dynamics Curve Tool for three-point cubic Bezier curve editing, the Freehand Draw Tool for drawing any dynamic curve by hand, the Mathematical Formula Input Tool for entering precise math, and the Classic Shapes Tool (triangle, oval, polygon, invert shape...), the Advanced Velocity Editor gives you next level control over your composition's dynamics. Want a mathematically precise 20 bar crescendo? You got it. Want a mathematically correct 
$y(t) = 20 \cdot \sin(\pi t)$ 
sine wave? You got it.
<br>
<br>

**Advanced Grid System** 

The Advanced Grid is a powerful visual tool for precise note placement. It can be configured to any time signature or meter, including standard, complex, odd, and mixed. Its tempo can be freely adjusted without affecting the original MIDI file's structure or playback. The initial grid time signature remains active in the background, visible but uneditable. Users can change it manually by navigating to the settings menu.
<br>
<br>

**Standard Piano Roll Interface**

The primary UI facilitates the same standard piano roll note editing as most modern DAWs, enabling users to independently modify pitch, timing, duration, and velocity. Notes can be added, deleted, or adjusted by their start and end points. Any user familiar with a piano roll editor will be instantly at home.
<br>
<br>

**VST Integration** 

The application supports real-time audio playback through Virtual Studio Technology (VST) instruments (e.g., Kontakt, Spitfire LABS). However, it does not support the import, export, or editing of audio files.

**CLI Usage:** 
Options:

  -h, --help     Show this help message

  -c, --console  Force console mode (no GUI)

  -v, --verbose  Enable verbose logging

  --check-deps   Only check dependencies and exit
  