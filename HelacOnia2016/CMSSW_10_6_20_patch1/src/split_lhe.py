#!/usr/bin/env python3
import os
import argparse


def split_lhe_file(input_file, events_per_file=1000, output_dir=None, output_prefix=None):
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(input_file))
    os.makedirs(output_dir, exist_ok=True)

    if output_prefix is None:
        base = os.path.basename(input_file)
        if base.endswith(".lhe"):
            output_prefix = base[:-4]
        else:
            output_prefix = base

    with open(input_file, "r") as f:
        lines = f.readlines()

    header_lines = []
    footer_lines = []
    events = []

    in_event = False
    current_event = []
    first_event_seen = False

    for line in lines:
        stripped = line.strip()

        if stripped == "<event>":
            in_event = True
            first_event_seen = True
            current_event = [line]
            continue

        if in_event:
            current_event.append(line)
            if stripped == "</event>":
                events.append(current_event)
                current_event = []
                in_event = False
            continue

        if not first_event_seen:
            header_lines.append(line)
        else:
            footer_lines.append(line)

    if in_event:
        raise RuntimeError("Malformed LHE file: found '<event>' without matching '</event>'.")

    n_events = len(events)
    if n_events == 0:
        raise RuntimeError("No <event> blocks found in the input file.")

    n_chunks = (n_events + events_per_file - 1) // events_per_file

    output_files = []

    for i in range(n_chunks):
        start = i * events_per_file
        end = min((i + 1) * events_per_file, n_events)
        chunk_events = events[start:end]

        out_name = f"{output_prefix}_part{i+1:03d}.lhe"
        out_path = os.path.join(output_dir, out_name)

        with open(out_path, "w") as out:
            for line in header_lines:
                out.write(line)

            for ev in chunk_events:
                for line in ev:
                    out.write(line)

            for line in footer_lines:
                out.write(line)

        output_files.append((out_path, end - start))

    print(f"Input file: {input_file}")
    print(f"Total events: {n_events}")
    print(f"Events per file: {events_per_file}")
    print(f"Number of output files: {n_chunks}")
    print()

    for path, nev in output_files:
        print(f"{path}    events = {nev}")


def main():
    parser = argparse.ArgumentParser(description="Split an LHE file into smaller LHE files by number of events.")
    parser.add_argument("input_file", help="Input LHE file")
    parser.add_argument("-n", "--events-per-file", type=int, default=1000,
                        help="Number of events per output file (default: 1000)")
    parser.add_argument("-o", "--output-dir", default=None,
                        help="Output directory (default: same as input file)")
    parser.add_argument("-p", "--prefix", default=None,
                        help="Output file prefix (default: input filename without .lhe)")
    args = parser.parse_args()

    split_lhe_file(
        input_file=args.input_file,
        events_per_file=args.events_per_file,
        output_dir=args.output_dir,
        output_prefix=args.prefix
    )


if __name__ == "__main__":
    main()