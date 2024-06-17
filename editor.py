# In-house website editor used for the development of dareaquatics/dare-website.
# Developed by Ryan Lu 

#!/usr/bin/env python3

import os
import subprocess
import sys
import requests
from bs4 import BeautifulSoup, Comment
import git
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from PIL import Image, ImageTk
import logging
from datetime import datetime

REPO_URL = 'https://github.com/dareaquatics/dare-website'
LOCAL_REPO_PATH = 'dare-website'
ASSET_DIR = 'assets/img/portfolio'

# Configure logging for GUI console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TextEditorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.repo_path = LOCAL_REPO_PATH
        self.html_files = []
        self.soup = None
        self.current_file = None
        self.editable_texts = None
        self.text_changed = False
        self.original_html_content = None

        self.title("DARE Aquatics Website Editor")
        self.geometry("900x700")

        self.create_widgets()
        self.init_repo()

    def create_widgets(self):
        self.file_label = ttk.Label(self, text="Select the HTML file:")
        self.file_label.grid(row=0, column=0, pady=10, padx=10, sticky='w')

        self.file_dropdown = ttk.Combobox(self, values=self.html_files, state="readonly")
        self.file_dropdown.grid(row=0, column=1, pady=5, padx=10, sticky='ew')
        self.file_dropdown.bind("<<ComboboxSelected>>", self.fetch_content)

        self.fetch_button = ttk.Button(self, text="Refetch Content", command=self.fetch_content)
        self.fetch_button.grid(row=0, column=2, pady=10, padx=10, sticky='e')

        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=1, column=0, columnspan=3, pady=10, padx=10, sticky='nsew')

        self.text_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.text_tab, text="Edit Text")

        self.text_listbox = tk.Listbox(self.text_tab, height=15, width=80)
        self.text_listbox.pack(pady=10)

        self.edit_button = ttk.Button(self.text_tab, text="Edit Selected Text", command=self.edit_text_prompt)
        self.edit_button.pack(pady=10)

        self.add_button = ttk.Button(self.text_tab, text="Add New Text", command=self.add_text_prompt)
        self.add_button.pack(pady=10)

        self.commit_button = ttk.Button(self.text_tab, text="Commit Changes", command=self.commit_changes_prompt)
        self.commit_button.pack(pady=10)
        self.commit_button.config(state=tk.DISABLED)

        self.image_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.image_tab, text="Manage Images")

        self.image_note_label = ttk.Label(self.image_tab, text="Images are from assets/img/portfolio")
        self.image_note_label.pack(pady=5)

        self.upload_button = ttk.Button(self.image_tab, text="Upload Image", command=self.upload_image_prompt)
        self.upload_button.pack(pady=10)

        self.delete_button = ttk.Button(self.image_tab, text="Delete Image", command=self.delete_image_prompt)
        self.delete_button.pack(pady=10)

        self.image_listbox = tk.Listbox(self.image_tab, height=15, width=80)
        self.image_listbox.pack(pady=10)
        self.image_listbox.bind('<<ListboxSelect>>', self.preview_image)

        self.image_label = ttk.Label(self.image_tab)
        self.image_label.pack(pady=10)

        self.commit_image_button = ttk.Button(self.image_tab, text="Commit Changes", command=self.commit_changes_prompt)
        self.commit_image_button.pack(pady=10)

        self.link_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.link_tab, text="Edit Links")

        self.link_listbox = tk.Listbox(self.link_tab, height=15, width=80)
        self.link_listbox.pack(pady=10)

        self.edit_link_button = ttk.Button(self.link_tab, text="Edit Selected Link", command=self.edit_link_prompt)
        self.edit_link_button.pack(pady=10)

        self.commit_link_button = ttk.Button(self.link_tab, text="Commit Link Changes", command=self.commit_changes_prompt)
        self.commit_link_button.pack(pady=10)

        self.directory_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.directory_tab, text="Directory Overview")

        self.directory_tree = scrolledtext.ScrolledText(self.directory_tab, wrap=tk.WORD, height=15)
        self.directory_tree.pack(pady=10, fill=tk.BOTH, expand=True)

        self.update_button = ttk.Button(self.directory_tab, text="Update", command=self.update_directory_overview)
        self.update_button.pack(pady=5)

        self.styling_help_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.styling_help_tab, text="HTML Styling Help")

        self.styling_help_text = scrolledtext.ScrolledText(self.styling_help_tab, wrap=tk.WORD)
        self.styling_help_text.pack(fill=tk.BOTH, expand=True)
        self.populate_styling_help()

        self.commit_history_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.commit_history_tab, text="Commit History")

        self.commit_history_listbox = tk.Listbox(self.commit_history_tab, height=15, width=80)
        self.commit_history_listbox.pack(pady=10)
        self.commit_history_listbox.bind('<<ListboxSelect>>', self.show_commit_details)

        self.commit_details_text = scrolledtext.ScrolledText(self.commit_history_tab, wrap=tk.WORD)
        self.commit_details_text.pack(fill=tk.BOTH, expand=True)

        self.console_frame = ttk.Frame(self)
        self.console_frame.grid(row=2, column=0, columnspan=3, pady=10, padx=10, sticky='nsew')

        self.console_log = scrolledtext.ScrolledText(self.console_frame, state='disabled', height=10, wrap=tk.WORD)
        self.console_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.console_scrollbar = ttk.Scrollbar(self.console_frame, orient=tk.VERTICAL, command=self.console_log.yview)
        self.console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console_log.config(yscrollcommand=self.console_scrollbar.set)

        self.log_level_label = ttk.Label(self.console_frame, text="Log Level:")
        self.log_level_label.pack(side=tk.LEFT, padx=5)

        self.log_level_combobox = ttk.Combobox(self.console_frame, values=["DEBUG", "INFO", "WARNING", "ERROR"], state="readonly")
        self.log_level_combobox.current(1)  # Default to INFO
        self.log_level_combobox.pack(side=tk.LEFT, padx=5)
        self.log_level_combobox.bind("<<ComboboxSelected>>", self.set_log_level)

        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def set_log_level(self, event):
        selected_level = self.log_level_combobox.get()
        level = getattr(logging, selected_level, logging.INFO)
        logger.setLevel(level)
        log_message(self.console_log, f"Log level set to {selected_level}", level=logging.INFO)

    def log_message(self, message, level=logging.INFO):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = f"{timestamp} - {logging.getLevelName(level)}: {message}"
        if level == logging.INFO:
            logger.info(full_message)
        elif level == logging.WARNING:
            logger.warning(full_message)
        elif level == logging.ERROR:
            logger.error(full_message)
        elif level == logging.DEBUG:
            logger.debug(full_message)
        self.console_log.config(state='normal')
        self.console_log.insert(tk.END, full_message + "\n")
        self.console_log.config(state='disabled')
        self.console_log.yview(tk.END)

    def update_directory_overview(self):
        try:
            tree_output = self.generate_tree_view(self.repo_path)
            self.directory_tree.config(state='normal')
            self.directory_tree.delete(1.0, tk.END)
            self.directory_tree.insert(tk.END, tree_output)
            self.directory_tree.config(state='disabled')
            self.log_message("Directory overview updated.", level=logging.INFO)
        except Exception as e:
            self.log_message(f"Error updating directory overview: {e}", level=logging.ERROR)

    def generate_tree_view(self, startpath):
        tree = []
        for root, dirs, files in os.walk(startpath):
            level = root.replace(startpath, '').count(os.sep)
            indent = ' ' * 4 * (level)
            tree.append(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                tree.append(f"{subindent}{f}")
        return "\n".join(tree)

    def init_repo(self):
        clone_repo(REPO_URL, self.repo_path, self.console_log)
        check_and_install_dependencies(self.console_log)
        self.html_files = fetch_html_files(self.repo_path)
        self.populate_html_files_dropdown()
        self.populate_commit_history()
        self.update_directory_overview()

    def populate_html_files_dropdown(self):
        self.file_dropdown.config(values=self.html_files)

    def fetch_content(self, event=None):
        selected_file = self.file_dropdown.get()
        if selected_file:
            self.current_file = selected_file
            self.soup, self.original_html_content = fetch_html_content(self.repo_path, selected_file)
            if self.soup:
                self.editable_texts = list_editable_text(self.soup)
                self.display_texts()
                self.display_links()
                self.display_images()
                self.log_message(f"Loaded content from {selected_file}", level=logging.INFO)
            else:
                messagebox.showerror("Error", "Failed to fetch HTML content.")
        else:
            messagebox.showwarning("Warning", "No HTML file selected.")

    def display_texts(self):
        self.text_listbox.delete(0, tk.END)
        for i, text_info in self.editable_texts.items():
            display_text = text_info['display_text']
            self.text_listbox.insert(tk.END, f"{i}: {display_text}")

    def display_links(self):
        self.link_listbox.delete(0, tk.END)
        for i, link in enumerate(self.soup.find_all('a', href=True)):
            self.link_listbox.insert(tk.END, f"{i}: {link.get_text()[:50]} ({link['href']})")

    def display_images(self):
        self.image_listbox.delete(0, tk.END)
        for root, _, files in os.walk(os.path.join(self.repo_path, ASSET_DIR)):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    file_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                    self.image_listbox.insert(tk.END, file_path)

    def edit_text_prompt(self):
        try:
            selected_index = self.text_listbox.curselection()[0]
            selected_text = self.editable_texts[selected_index]['tag'].decode_contents()
            edit_window = tk.Toplevel(self)
            edit_window.title("Edit Text")
            editor = scrolledtext.ScrolledText(edit_window, wrap=tk.WORD, width=80, height=20)
            editor.pack(pady=10)
            editor.insert(tk.END, selected_text)
            save_button = ttk.Button(edit_window, text="Save", command=lambda: self.save_text(editor, selected_index, edit_window))
            save_button.pack(pady=10)
        except IndexError:
            messagebox.showwarning("Warning", "No text selected.")

    def save_text(self, editor, text_id, window):
        new_text = editor.get("1.0", tk.END).strip()
        self.soup = edit_text(self.soup, text_id, new_text, self.editable_texts)
        self.display_texts()
        window.destroy()
        self.commit_button.config(state=tk.NORMAL)
        self.text_changed = True

    def add_text_prompt(self):
        add_window = tk.Toplevel(self)
        add_window.title("Add New Text")
        tag_label = ttk.Label(add_window, text="HTML Tag:")
        tag_label.pack(pady=5)
        tag_entry = ttk.Entry(add_window, width=50)
        tag_entry.pack(pady=5)
        text_label = ttk.Label(add_window, text="Text Content:")
        text_label.pack(pady=5)
        text_entry = scrolledtext.ScrolledText(add_window, wrap=tk.WORD, width=50, height=10)
        text_entry.pack(pady=5)
        add_button = ttk.Button(add_window, text="Add", command=lambda: self.add_text(tag_entry.get(), text_entry.get("1.0", tk.END).strip(), add_window))
        add_button.pack(pady=10)

    def add_text(self, tag, text, window):
        if tag and text:
            self.soup = add_text(self.soup, tag, text)
            self.display_texts()
            window.destroy()
            self.commit_button.config(state=tk.NORMAL)
            self.text_changed = True
        else:
            messagebox.showerror("Error", "Tag and text content cannot be empty.")

    def commit_changes_prompt(self):
        commit_window = tk.Toplevel(self)
        commit_window.title("Commit Changes")
        commit_message_label = ttk.Label(commit_window, text="Commit Message:")
        commit_message_label.pack(pady=5)
        commit_message_entry = ttk.Entry(commit_window, width=50)
        commit_message_entry.pack(pady=5)
        commit_description_label = ttk.Label(commit_window, text="Commit Description (optional):")
        commit_description_label.pack(pady=5)
        commit_description_text = scrolledtext.ScrolledText(commit_window, wrap=tk.WORD, width=50, height=10)
        commit_description_text.pack(pady=5)
        commit_button = ttk.Button(commit_window, text="Commit", command=lambda: self.commit_changes(commit_message_entry.get(), commit_description_text.get("1.0", tk.END).strip(), commit_window))
        commit_button.pack(pady=10)

    def commit_changes(self, message, description, window):
        if message:
            if self.text_changed:
                if not save_html_content(os.path.join(self.repo_path, self.current_file), self.soup, self.original_html_content):
                    messagebox.showerror("Error", "Failed to save changes.")
                    return
            commit_changes(self.repo_path, message, description, self.console_log)
            window.destroy()
            messagebox.showinfo("Success", "Changes committed successfully.")
            self.commit_button.config(state=tk.DISABLED)
            self.text_changed = False
        else:
            messagebox.showerror("Error", "Commit message cannot be empty.")
        self.populate_commit_history()

    def upload_image_prompt(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            upload_image(self.repo_path, file_path, ASSET_DIR, self.console_log)
            self.display_images()

    def delete_image_prompt(self):
        try:
            selected_index = self.image_listbox.curselection()[0]
            file_path = self.image_listbox.get(selected_index)
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {file_path}?")
            if confirm:
                delete_image(self.repo_path, file_path, self.console_log)
                self.display_images()
        except IndexError:
            messagebox.showwarning("Warning", "No image selected.")

    def preview_image(self, event):
        try:
            selected_index = self.image_listbox.curselection()[0]
            file_path = os.path.join(self.repo_path, self.image_listbox.get(selected_index))
            image = Image.open(file_path)
            image.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo)
            self.image_label.image = photo
        except Exception as e:
            self.log_message(f"Error previewing image: {e}", level=logging.ERROR)

    def edit_link_prompt(self):
        try:
            selected_index = self.link_listbox.curselection()[0]
            link_tag = self.soup.find_all('a', href=True)[selected_index]
            current_text = link_tag.get_text()
            current_href = link_tag['href']
            edit_window = tk.Toplevel(self)
            edit_window.title("Edit Link")
            text_label = ttk.Label(edit_window, text="Link Text:")
            text_label.pack(pady=5)
            text_entry = ttk.Entry(edit_window, width=50)
            text_entry.pack(pady=5)
            text_entry.insert(tk.END, current_text)
            href_label = ttk.Label(edit_window, text="Link URL:")
            href_label.pack(pady=5)
            href_entry = ttk.Entry(edit_window, width=50)
            href_entry.pack(pady=5)
            href_entry.insert(tk.END, current_href)
            save_button = ttk.Button(edit_window, text="Save", command=lambda: self.save_link(link_tag, text_entry.get(), href_entry.get(), edit_window))
            save_button.pack(pady=10)
        except IndexError:
            messagebox.showwarning("Warning", "No link selected.")

    def save_link(self, link_tag, new_text, new_href, window):
        try:
            if new_text != link_tag.get_text():
                link_tag.string.replace_with(new_text)
            if new_href != link_tag['href']:
                link_tag['href'] = new_href
            self.display_links()
            window.destroy()
            self.commit_button.config(state=tk.NORMAL)
            self.text_changed = True
        except Exception as e:
            self.log_message(f"Error saving link: {e}", level=logging.ERROR)
            messagebox.showerror("Error", f"Failed to save link: {e}")

    def populate_styling_help(self):
        styling_help_content = """
        <b> - Bold: Use to make text bold.
        <strong> - Strong: Similar to <b>, but indicates importance.
        <i> - Italic: Use to italicize text.
        <em> - Emphasis: Similar to <i>, but indicates emphasis.
        <u> - Underline: Use to underline text.
        <code> - Code: Use to display code snippets.
        """
        self.styling_help_text.insert(tk.END, styling_help_content)
        self.styling_help_text.config(state=tk.DISABLED)

    def populate_commit_history(self):
        self.commit_history_listbox.delete(0, tk.END)
        repo = git.Repo(self.repo_path)
        branch = 'main'
        commits = list(repo.iter_commits(branch, max_count=10))
        for commit in commits:
            self.commit_history_listbox.insert(tk.END, f"{commit.hexsha[:7]} - {commit.message.splitlines()[0]}")

    def show_commit_details(self, event):
        try:
            selected_index = self.commit_history_listbox.curselection()[0]
            commit_hash = self.commit_history_listbox.get(selected_index).split(" ")[0]
            repo = git.Repo(self.repo_path)
            commit = repo.commit(commit_hash)
            commit_details = f"""
            Commit ID: {commit.hexsha}
            Author: {commit.author}
            Date: {commit.committed_datetime}
            Message: {commit.message}
            Files Changed:
            """
            for diff in commit.diff(commit.parents[0]):
                commit_details += f"\n{diff.a_path} ({diff.change_type})"
            self.commit_details_text.config(state=tk.NORMAL)
            self.commit_details_text.delete(1.0, tk.END)
            self.commit_details_text.insert(tk.END, commit_details)
            self.commit_details_text.config(state=tk.DISABLED)
        except IndexError:
            messagebox.showwarning("Warning", "No commit selected.")

def log_message(console, message, level=logging.INFO):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"{timestamp} - {logging.getLevelName(level)}: {message}"
    if level == logging.INFO:
        logger.info(full_message)
    elif level == logging.WARNING:
        logger.warning(full_message)
    elif level == logging.ERROR:
        logger.error(full_message)
    elif level == logging.DEBUG:
        logger.debug(full_message)
    console.config(state='normal')
    console.insert(tk.END, full_message + "\n")
    console.config(state='disabled')
    console.yview(tk.END)

def check_and_install_dependencies(console):
    dependencies = ['requests', 'beautifulsoup4', 'gitpython', 'pillow']
    missing_dependencies = [dep for dep in dependencies if subprocess.call(['pip', 'show', dep]) != 0]
    if missing_dependencies:
        install = messagebox.askyesno("Install Dependencies", f"Missing dependencies: {', '.join(missing_dependencies)}. Install now?")
        if install:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing_dependencies])
            log_message(console, f"Installed missing dependencies: {', '.join(missing_dependencies)}")

def clone_repo(repo_url, local_path, console):
    try:
        if not os.path.exists(local_path):
            git.Repo.clone_from(repo_url, local_path)
            log_message(console, f"Cloned repository to {local_path}")
        else:
            log_message(console, f"Repository already exists at {local_path}")
    except Exception as e:
        log_message(console, f"Error cloning repository: {e}", level=logging.ERROR)

def fetch_html_files(repo_path):
    html_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.relpath(os.path.join(root, file), repo_path))
    return html_files

def fetch_html_content(repo_path, file_path):
    try:
        with open(os.path.join(repo_path, file_path), 'r', encoding='utf-8') as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
            for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
                comment.extract()
            return soup, content
    except Exception as e:
        logger.error(f"Error fetching HTML content: {e}")
        return None, None

def list_editable_text(soup):
    editable_texts = {}
    unique_texts = set()
    for i, tag in enumerate(soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])):
        text = tag.decode_contents().strip()
        if text and text not in unique_texts:
            if len(text) > 50:
                text_display = text[:47] + '...'
            else:
                text_display = text
            editable_texts[i] = {'tag': tag, 'display_text': text_display}
            unique_texts.add(text)
    return editable_texts

def edit_text(soup, text_id, new_text, editable_texts):
    try:
        editable_text = editable_texts[text_id]['tag']
        editable_text.clear()
        editable_text.append(new_text)
        return soup
    except Exception as e:
        logger.error(f"Error editing text: {e}")
        return soup

def add_text(soup, tag_name, new_text):
    try:
        new_tag = soup.new_tag(tag_name)
        new_tag.string = new_text
        soup.body.append(new_tag)
        return soup
    except Exception as e:
        logger.error(f"Error adding text: {e}")
        return soup

def save_html_content(file_path, soup, original_content):
    try:
        new_content = str(soup)
        original_lines = original_content.splitlines()
        new_lines = new_content.splitlines()
        
        # Ensure closing </html> tag is present
        if not new_lines[-1].strip().lower().endswith('</html>'):
            new_lines.append('</html>')
        
        updated_lines = []
        for original_line, new_line in zip(original_lines, new_lines):
            if original_line.strip() != new_line.strip():
                updated_lines.append(new_line)
            else:
                updated_lines.append(original_line)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('\n'.join(updated_lines))
        return True
    except Exception as e:
        logger.error(f"Error saving HTML content: {e}")
        return False

def pull_latest_changes(repo_path, console):
    try:
        repo = git.Repo(repo_path)
        origin = repo.remotes.origin
        origin.pull()
        log_message(console, "Pulled latest changes from repository")
    except git.GitCommandError as e:
        log_message(console, f"Error pulling latest changes: {e}", level=logging.ERROR)

def commit_changes(repo_path, commit_message, commit_description, console):
    try:
        pull_latest_changes(repo_path, console)
        repo = git.Repo(repo_path)
        repo.git.add(update=True)
        repo.index.commit(f"{commit_message}\n\n{commit_description}" if commit_description else commit_message)
        origin = repo.remote(name='origin')
        origin.push()
        log_message(console, "Committed and pushed changes")
    except git.GitCommandError as e:
        log_message(console, f"Error committing changes: {e}", level=logging.ERROR)

def upload_image(repo_path, file_path, target_dir, console):
    try:
        repo = git.Repo(repo_path)
        target_path = os.path.join(repo.working_tree_dir, target_dir, os.path.basename(file_path))
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        os.replace(file_path, target_path)
        repo.git.add(target_path)
        repo.index.commit(f"Add image {os.path.basename(file_path)}")
        origin = repo.remote(name='origin')
        origin.push()
        log_message(console, f"Uploaded and committed image: {os.path.basename(file_path)}")
    except git.GitCommandError as e:
        log_message(console, f"Error uploading image: {e}", level=logging.ERROR)
    except Exception as e:
        log_message(console, f"Unexpected error: {e}", level=logging.ERROR)

def delete_image(repo_path, file_path, console):
    try:
        repo = git.Repo(repo_path)
        target_path = os.path.join(repo.working_tree_dir, file_path)
        os.remove(target_path)
        repo.git.add(target_path)
        repo.index.commit(f"Delete image {os.path.basename(file_path)}")
        origin = repo.remote(name='origin')
        origin.push()
        log_message(console, f"Deleted and committed image: {file_path}")
    except git.GitCommandError as e:
        log_message(console, f"Error deleting image: {e}", level=logging.ERROR)
    except FileNotFoundError:
        log_message(console, f"File not found: {file_path}", level=logging.ERROR)

if __name__ == "__main__":
    app = TextEditorApp()
    app.mainloop()
