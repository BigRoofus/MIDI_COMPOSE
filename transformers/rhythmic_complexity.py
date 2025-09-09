# This feature intelligently simplifies MIDI by reducing note density 
# and merging consecutive notes. It allows users to specify a target 
# rhythmic resolution, such as converting a passage with 64th notes 
# into 16th notes. The tool also automatically combines short, 
# repeated notes on the same staff into a single, longer note to 
# create a smoother and more streamlined musical line.

# This feature can also do the exact opposite by adding extra notes 
# into MIDI data that has sparse, or longer notes. Users can specify 
# a target rhythmic resolution here as well, such as adding 64th notes 
# into a passage with only half notes. The new added notes are random 
# but based on high connosnance levels such as Octaves, Perfect Fifths, 
# Perfect Fourths, Major Thirds, and Minor Thirds, as relating the 
# original MIDI data.
