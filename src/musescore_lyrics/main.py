import requests
import lxml
import pyperclip
import re
import sys
import tkinter as tk

def get_hyphenated_word(input_list):
    word_list = input_list.copy()
    search_string = '+'.join(word_list)

    response = requests.get(f'https://helyesiras.mta.hu/helyesiras/default/hyph?q={search_string}')
    doc = lxml.etree.HTML(response.text) # type: ignore
    answers = doc.xpath('//ul[@class="result"]/li/i')

    for i,answer in enumerate(answers):
        stripped = answer.text.strip().replace('|', '').replace('-', '')
        word_list[i] = word_list[i].replace(stripped, answer.text.replace('|', '').split(',')[0])

    return word_list

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

    tk.Label(top_frame, text="Song ID:").pack(side='left')
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
    original_text = tk.Text(left_frame, wrap='word', width=60, height=30)
    original_text.pack(fill='both', expand=True)
    middle.add(left_frame)

    # Processed (syllabified) lyrics panel
    right_frame = tk.Frame(middle)
    tk.Label(right_frame, text="Syllabified Lyrics").pack(anchor='w')
    processed_text = tk.Text(right_frame, wrap='word', width=60, height=30)
    processed_text.pack(fill='both', expand=True)
    middle.add(right_frame)

    # Helper to convert text widget content to lyrics structure and back
    def text_to_lyrics(text_widget):
        raw = text_widget.get('1.0', 'end').strip()
        if raw == '':
            return []
        lines = raw.split('\n\n')
        return [[line.strip()] for line in lines if line.strip() != '']

    def lyrics_to_text(lyrics):
        return '\n\n'.join(v[0] for v in lyrics)

    # Actions
    def fetch_song():
        sid = songid_var.get().strip()
        if not sid:
            status_var.set("Provide a Song ID")
            return
        status_var.set("Fetching...")
        root.update_idletasks()
        try:
            url = f'https://www.songpraise.com/api/song/{sid}'
            lyrics = get_song_lyrics(url)
            original_text.delete('1.0', 'end')
            original_text.insert('1.0', lyrics_to_text(lyrics))
            processed_text.delete('1.0', 'end')
            status_var.set("Fetched and saved to original_lyrics.txt")
        except Exception as e:
            status_var.set(f"Error: {e}")

    def load_from_file():
        try:
            with open('original_lyrics.txt', 'r', encoding='utf-8') as f:
                data = f.read().strip()
            original_text.delete('1.0', 'end')
            original_text.insert('1.0', data)
            status_var.set("Loaded original_lyrics.txt")
        except Exception as e:
            status_var.set(f"Load error: {e}")

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
            status_var.set("Processed and saved to lyrics.txt")
        except Exception as e:
            status_var.set(f"Processing error: {e}")

    def save_original():
        try:
            with open('original_lyrics.txt', 'w', encoding='utf-8') as f:
                f.write(original_text.get('1.0', 'end').strip())
            status_var.set("Original saved to original_lyrics.txt")
        except Exception as e:
            status_var.set(f"Save error: {e}")

    def save_processed():
        try:
            with open('lyrics.txt', 'w', encoding='utf-8') as f:
                f.write(processed_text.get('1.0', 'end').strip())
            status_var.set("Processed saved to lyrics.txt")
        except Exception as e:
            status_var.set(f"Save error: {e}")

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
        status_var.set("Cleared")
        try:
            pyperclip.copy('')
        except:
            pass

    # Bottom frame: control buttons
    bottom = tk.Frame(root)
    bottom.pack(fill='x', padx=8, pady=(0,8))

    tk.Button(bottom, text="Fetch", command=fetch_song).pack(side='left')
    tk.Button(bottom, text="Load file", command=load_from_file).pack(side='left', padx=4)
    tk.Button(bottom, text="Process", command=process_current).pack(side='left', padx=4)
    tk.Button(bottom, text="Save Original", command=save_original).pack(side='left', padx=4)
    tk.Button(bottom, text="Save Processed", command=save_processed).pack(side='left', padx=4)
    tk.Button(bottom, text="Copy Processed", command=copy_processed).pack(side='left', padx=4)
    tk.Button(bottom, text="Clear All", command=clear_all).pack(side='left', padx=4)
    tk.Button(bottom, text="Quit", command=root.quit).pack(side='right')

    # Pre-fill song id from argv if provided
    try:
        if len(sys.argv) > 1:
            songid_var.set(sys.argv[1])
    except:
        pass

    root.mainloop()

if __name__ == "__main__":
    main()