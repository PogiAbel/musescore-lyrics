import requests
import pyperclip
import re
import sys
import tkinter as tk
import pyphen

from musescore_lyrics.tools import CUSTOM_TOOLS, run_tool

def get_hyphenated_word(input_list):
    dic = pyphen.Pyphen(lang="hu_HU")
    result = []

    for word in input_list:
        hyphenated = dic.inserted(word)
        result.append(hyphenated)

    return result

def get_id_from_url(url: str):
    return url.split("/")[-1]

def normalize(string):
    out = re.sub(r'[\d.]', '', string)
    out = re.sub(r'[\n]', ' ', out)
    out = re.sub(r'[\/:]+', ' ', out)
    out = re.sub(r'[\:]+', ' ', out)
    
    return out

def get_word_list(lyrics):
    word_list = []
    for line in lyrics:
        word_list += line.split()

    return word_list

def get_song_lyrics(url):
    response = requests.get(url)
    result = response.json()
    lyrics = [[normalize(x['text'])] for x in result['songVerseDTOS']]
    return lyrics

def process_lyrics(lyrics):
    for verse in lyrics:
        word_list = get_word_list(verse)
        hyphenated = get_hyphenated_word(word_list)
        verse[0] = ' '.join(hyphenated)

def main():
    # Simple Tkinter GUI to fetch, edit and process lyrics
    root = tk.Tk()
    root.title("Lyrics Syllabifier")

    # Top frame: Song ID entry and buttons
    top_frame = tk.Frame(root)
    top_frame.pack(fill='x', padx=8, pady=6)

    tk.Label(top_frame, text="Song url:").pack(side='left')
    songid_var = tk.StringVar()
    songid_entry = tk.Entry(top_frame, textvariable=songid_var, width=20)
    songid_entry.pack(side='left', padx=(4, 8))

    status_var = tk.StringVar(value="Idle")
    status_label = tk.Label(top_frame, textvariable=status_var)
    status_label.pack(side='right')

    # Middle frame: two text boxes for original and processed lyrics
    middle = tk.PanedWindow(root, sashrelief='raised', sashwidth=6, orient='horizontal')
    middle.pack(fill='both', expand=True, padx=8, pady=6)

    # Original lyrics panel
    left_frame = tk.Frame(middle)
    tk.Label(left_frame, text="Original / Edited Lyrics").pack(anchor='w')
    original_text = tk.Text(left_frame, wrap='word', width=60, height=15)
    original_text.pack(fill='both', expand=True)
    middle.add(left_frame)

    # Processed (syllabified) lyrics panel
    right_frame = tk.Frame(middle)
    tk.Label(right_frame, text="Syllabified Lyrics").pack(anchor='w')
    processed_text = tk.Text(right_frame, wrap='word', width=60, height=15)
    processed_text.pack(fill='both', expand=True)
    middle.add(right_frame)

    # Configure highlight tag for processed text
    processed_text.tag_configure('highlight', background='yellow', foreground='black')

    # Helper to convert text widget content to lyrics structure and back
    def text_to_lyrics(text_widget):
        raw = text_widget.get('1.0', 'end').strip()
        if raw == '':
            return []
        lines = raw.split('\n\n')
        return [[line.strip()] for line in lines if line.strip() != '']

    def lyrics_to_text(lyrics):
        return '\n\n'.join(v[0] for v in lyrics)

    def extract_and_clean_highlights(text_content):
        """Extract highlighted words and return clean text."""
        pattern = r'<hl>([^<]+)</hl>'
        highlighted_words = [match.group(1) for match in re.finditer(pattern, text_content)]
        clean_text = re.sub(pattern, r'\1', text_content)
        return clean_text, highlighted_words

    def apply_highlight_tags(text_widget, highlighted_words):
        """Apply highlight tags to words in the text widget."""
        text_widget.tag_remove('highlight', '1.0', 'end')
        word_pattern = re.compile(r"\b([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)\b", re.UNICODE)
        highlighted_set = set(highlighted_words)
        
        lines = text_widget.get('1.0', 'end').split('\n')
        for line_num, line in enumerate(lines, start=1):
            for match in word_pattern.finditer(line):
                word = match.group(1)
                if word in highlighted_set:
                    start_idx = f"{line_num}.{match.start()}"
                    end_idx = f"{line_num}.{match.end()}"
                    text_widget.tag_add('highlight', start_idx, end_idx)

    # Actions
    def fetch_song():
        surl = songid_var.get().strip()
        if not surl:
            status_var.set("Provide a Song url")
            return
        status_var.set("Fetching...")
        root.update_idletasks()
        try:
            sid = get_id_from_url(surl)
            url = f'https://www.songpraise.com/api/song/{sid}'
            lyrics = get_song_lyrics(url)
            original_text.delete('1.0', 'end')
            original_text.insert('1.0', lyrics_to_text(lyrics))
            processed_text.delete('1.0', 'end')
            status_var.set("Fetched lyrics")
        except Exception as e:
            status_var.set(f"Error: {e}")

    def process_current():
        lyrics = text_to_lyrics(original_text)
        if not lyrics:
            status_var.set("No lyrics to process")
            return
        status_var.set("Processing...")
        root.update_idletasks()
        try:
            process_lyrics(lyrics)
            processed_text.delete('1.0', 'end')
            processed_text.insert('1.0', lyrics_to_text(lyrics))
            status_var.set("Processed lyrics")
        except Exception as e:
            print(e)
            status_var.set(f"Processing error")

    def copy_processed():
        try:
            pyperclip.copy(processed_text.get('1.0', 'end').strip())
            status_var.set("Processed copied to clipboard")
        except Exception as e:
            status_var.set(f"Clipboard error: {e}")
    def clear_all():
        # clear both text areas and reset status (also clear clipboard if available)
        original_text.delete('1.0', 'end')
        processed_text.delete('1.0', 'end')
        songid_entry.delete(0, 'end')
        selected_tool_var.set("Select a custom tool")
        tool_description_var.set("Select a custom tool to run")
        status_var.set("Cleared")
        try:
            pyperclip.copy('')
        except:
            pass

    def populate_tool_list():
        menu = tool_dropdown['menu']
        menu.delete(0, 'end')
        menu.add_command(label="Select a custom tool", command=lambda: selected_tool_var.set("Select a custom tool"))
        for tool in CUSTOM_TOOLS:
            menu.add_command(label=tool.name, command=lambda name=tool.name: selected_tool_var.set(name))

    def on_tool_selected(*args):
        tool_name = selected_tool_var.get()
        if tool_name == "Select a custom tool":
            tool_description_var.set("Select a custom tool to run")
            return
        for tool in CUSTOM_TOOLS:
            if tool.name == tool_name:
                tool_description_var.set(tool.description)
                return
        tool_description_var.set("Select a custom tool to run")

    def run_selected_tool():
        tool_name = selected_tool_var.get()
        if tool_name == "Select a custom tool":
            status_var.set("No custom tool selected")
            return

        tool = next((tool for tool in CUSTOM_TOOLS if tool.name == tool_name), None)
        if tool is None:
            status_var.set("Selected tool not found")
            return

        original_value = original_text.get('1.0', 'end').strip()
        processed_value = processed_text.get('1.0', 'end').strip()

        status_var.set(f"Running tool: {tool.name}")
        root.update_idletasks()

        try:
            new_original, new_processed = run_tool(tool, original_value, processed_value)
            original_text.delete('1.0', 'end')
            original_text.insert('1.0', new_original)
            processed_text.delete('1.0', 'end')
            clean_processed, highlighted_words = extract_and_clean_highlights(new_processed)
            processed_text.insert('1.0', clean_processed)
            apply_highlight_tags(processed_text, highlighted_words)
            status_var.set(f"Tool applied: {tool.name}")
        except Exception as e:
            status_var.set(f"Tool error: {e}")

    # Bottom frame: control buttons
    bottom = tk.Frame(root)
    bottom.pack(fill='x', padx=8, pady=(0,8))

    controls_frame = tk.Frame(bottom)
    controls_frame.pack(side='left')

    tk.Button(controls_frame, text="Fetch", command=fetch_song).pack(side='left')
    tk.Button(controls_frame, text="Process", command=process_current).pack(side='left', padx=4)
    tk.Button(controls_frame, text="Copy", command=copy_processed).pack(side='left', padx=4)
    tk.Button(controls_frame, text="Clear All", command=clear_all).pack(side='left', padx=4)
    tk.Button(controls_frame, text="Quit", command=root.quit).pack(side='left', padx=4)

    tools_frame = tk.Frame(bottom)
    tools_frame.pack(side='right', fill='x', expand=True)

    tk.Label(tools_frame, text="Custom tools").pack(anchor='w')
    selected_tool_var = tk.StringVar(value="Select a custom tool")
    tool_dropdown = tk.OptionMenu(tools_frame, selected_tool_var, "Select a custom tool")
    tool_dropdown.config(width=28)
    tool_dropdown.pack(fill='x', pady=(2, 4))
    selected_tool_var.trace_add('write', on_tool_selected)

    tool_description_var = tk.StringVar(value="Select a custom tool to run")
    tk.Label(tools_frame, textvariable=tool_description_var, wraplength=360, justify='left').pack(anchor='w', pady=(2, 4))
    tk.Button(tools_frame, text="Run tool", command=run_selected_tool).pack(anchor='e')

    populate_tool_list()

    # Pre-fill song id from argv if provided
    try:
        if len(sys.argv) > 1:
            songid_var.set(sys.argv[1])
    except:
        pass

    root.mainloop()

if __name__ == "__main__":
    main()