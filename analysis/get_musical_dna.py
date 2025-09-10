import pretty_midi
import json
import os

def pitch_class(pitch):
    return pitch % 12

def jaccard_similarity(set1, set2):
    intersection = len(set(set1) & set(set2))
    union = len(set(set1) | set(set2))
    return intersection / union if union > 0 else 0

def analyze_midi_to_musdna(midi_path, similarity_threshold=0.7):
    pm = pretty_midi.PrettyMIDI(midi_path)
    
    # Estimate tempo and time signature
    ts = pm.time_signature_changes[0] if pm.time_signature_changes else pretty_midi.TimeSignature(4,4,0)
    meter = f"{ts.numerator}/{ts.denominator}"
    subdivision = 16

    tempo_changes = pm.get_tempo_changes()
    tempo = tempo_changes[1][0] if tempo_changes[1].size > 0 else 120
    sec_per_beat = 60.0 / tempo
    beats_per_measure = ts.numerator
    sec_per_measure = beats_per_measure * sec_per_beat

    # Flatten all notes with timing
    notes = []
    for inst_idx, inst in enumerate(pm.instruments):
        for note in inst.notes:
            notes.append({
                "start": note.start,
                "end": note.end,
                "pitch": pitch_class(note.pitch),
                "instrument": inst_idx
            })
    notes.sort(key=lambda n: n["start"])

    # Dynamic segmentation based on pitch set changes
    timeline = []
    form_letters = []
    segments = []
    current_segment = []
    last_pitch_set = set()

    for note in notes:
        current_segment.append(note)
        segment_pitch_set = set(n["pitch"] for n in current_segment)
        if len(last_pitch_set) > 0:
            sim = jaccard_similarity(segment_pitch_set, last_pitch_set)
            if sim < similarity_threshold:
                segments.append(current_segment[:-1])
                current_segment = [note]
                last_pitch_set = segment_pitch_set
        last_pitch_set = segment_pitch_set
    if current_segment:
        segments.append(current_segment)

    # Assign form letters
    letter_map = []
    form_string = ""
    for seg in segments:
        seg_pitch_set = set(n["pitch"] for n in seg)
        assigned = False
        for i, existing_set in enumerate(letter_map):
            if jaccard_similarity(seg_pitch_set, existing_set) >= similarity_threshold:
                form_string += chr(65+i)
                assigned = True
                break
        if not assigned:
            letter_map.append(seg_pitch_set)
            form_string += chr(65+len(letter_map)-1)

        # Motif: first 5 notes intervals/rhythms
        seg.sort(key=lambda n: n["start"])
        intervals = []
        rhythms = []
        for i in range(1, min(5, len(seg))):
            intervals.append(seg[i]["pitch"] - seg[i-1]["pitch"])
            rhythms.append(round((seg[i]["start"] - seg[i-1]["start"]) / sec_per_beat, 3))

        # Density: notes per measure
        density = len(seg)/beats_per_measure

        timeline.append({
            "count": round(seg[0]["start"] / sec_per_measure),
            "pitch_set": sorted(list(seg_pitch_set)),
            "motifs": [{"intervals": intervals, "rhythm": rhythms}],
            "density": density,
            "form": form_string[-1]
        })

    musdna = {
        "work_title": os.path.basename(midi_path),
        "timeline": timeline,
        "form_string": form_string,
        "rhythmic_grid": {"meter": meter, "subdivision": subdivision}
    }

    out_path = os.path.splitext(midi_path)[0] + ".musdna"
    with open(out_path, "w") as f:
        json.dump(musdna, f, indent=2)

    print(f"Saved musical DNA to {out_path}")


# Example usage
if __name__ == "__main__":
    analyze_midi_to_musdna("string_quartet.mid")
