import os
import sys
import subprocess
import threading
import requests
import zipfile
import shutil
import webbrowser
from pathlib import Path
from tkinter import *
from tkinter import ttk, filedialog, messagebox

class NDKAlignmentTool:
    def __init__(self, root):
        self.root = root
        self.root.title("SoPageAligner v1.0.1")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Set up styles for better cross-platform appearance
        self.setup_styles()
        
        self.ndk_path = StringVar()
        self.source_dir = StringVar()
        self.target_dir = StringVar()
        self.auto_detect_ndk = BooleanVar(value=True)
        self.selected_abis = {
            "arm64-v8a": BooleanVar(value=True),
            "armeabi-v7a": BooleanVar(value=True),
            "x86": BooleanVar(value=True),
            "x86_64": BooleanVar(value=True)
        }
        
        self.abi_formats = {
            "arm64-v8a": "elf64-littleaarch64",
            "armeabi-v7a": "elf32-littlearm",
            "x86": "elf32-i386",
            "x86_64": "elf64-x86-64"
        }
        
        self.setup_ui()
        self.auto_detect_ndk_location()
    
    def setup_styles(self):
        # Use system-specific styles for better cross-platform appearance
        style = ttk.Style()
        if sys.platform == "win32":
            style.theme_use('vista')
        elif sys.platform == "darwin":
            style.theme_use('aqua')
        else:
            style.theme_use('clam')
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(N, W, E, S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # NDK Path section
        ttk.Label(main_frame, text="NDK Path:").grid(row=0, column=0, sticky=W, pady=5)
        ndk_frame = ttk.Frame(main_frame)
        ndk_frame.grid(row=0, column=1, sticky=(W, E), pady=5)
        ndk_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(ndk_frame, textvariable=self.ndk_path).grid(row=0, column=0, sticky=(W, E))
        ttk.Button(ndk_frame, text="Browse", command=self.browse_ndk).grid(row=0, column=1, padx=(5, 0))
        ttk.Button(ndk_frame, text="Download NDK", command=self.download_ndk).grid(row=0, column=2, padx=(5, 0))
        
        ttk.Checkbutton(main_frame, text="Auto-detect NDK", variable=self.auto_detect_ndk, 
                       command=self.toggle_auto_detect).grid(row=0, column=2, sticky=W, pady=5, padx=(5, 0))
        
        # Source Directory section
        ttk.Label(main_frame, text="Source Directory:").grid(row=1, column=0, sticky=W, pady=5)
        source_frame = ttk.Frame(main_frame)
        source_frame.grid(row=1, column=1, sticky=(W, E), pady=5)
        source_frame.columnconfigure(0, weight=1)
        
        self.source_entry = ttk.Entry(source_frame, textvariable=self.source_dir)
        self.source_entry.grid(row=0, column=0, sticky=(W, E))
        ttk.Button(source_frame, text="Browse", command=self.browse_source).grid(row=0, column=1, padx=(5, 0))
        ttk.Button(source_frame, text="Open", command=self.open_source).grid(row=0, column=2, padx=(5, 0))
        
        # Target Directory section
        ttk.Label(main_frame, text="Target Directory:").grid(row=2, column=0, sticky=W, pady=5)
        target_frame = ttk.Frame(main_frame)
        target_frame.grid(row=2, column=1, sticky=(W, E), pady=5)
        target_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(target_frame, textvariable=self.target_dir).grid(row=0, column=0, sticky=(W, E))
        ttk.Button(target_frame, text="Browse", command=self.browse_target).grid(row=0, column=1, padx=(5, 0))
        
        # ABI selection
        ttk.Label(main_frame, text="Select ABIs:").grid(row=3, column=0, sticky=W, pady=5)
        abi_frame = ttk.Frame(main_frame)
        abi_frame.grid(row=3, column=1, sticky=(W, E), pady=5)
        
        for i, (abi, var) in enumerate(self.selected_abis.items()):
            ttk.Checkbutton(abi_frame, text=abi, variable=var).grid(row=0, column=i, padx=5)
        
        # Progress section
        ttk.Label(main_frame, text="Progress:").grid(row=4, column=0, sticky=W, pady=5)
        
        self.progress = ttk.Progressbar(main_frame, mode='determinate', maximum=100)
        self.progress.grid(row=4, column=1, sticky=(W, E), pady=5)
        
        self.progress_label = ttk.Label(main_frame, text="0%")
        self.progress_label.grid(row=4, column=2, padx=(5, 0))
        
        # Log section
        ttk.Label(main_frame, text="Log:").grid(row=5, column=0, sticky=W, pady=5)
        
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(W, E, N, S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = Text(log_frame, height=15, wrap=WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(W, E, N, S))
        scrollbar.grid(row=0, column=1, sticky=(N, S))
        
        # Button section
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Start Alignment", command=self.start_alignment).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Check for Updates", command=lambda: webbrowser.open("https://github.com/fzer0x")).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=RIGHT, padx=5)
    
    def toggle_auto_detect(self):
        if self.auto_detect_ndk.get():
            self.auto_detect_ndk_location()
    
    def auto_detect_ndk_location(self):
        possible_paths = []
        
        # Check common NDK installation paths
        if os.name == 'nt':  # Windows
            # Check Android Studio default location
            sdk_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk')
            if os.path.exists(sdk_path):
                ndk_dir = os.path.join(sdk_path, 'ndk')
                if os.path.exists(ndk_dir):
                    versions = [d for d in os.listdir(ndk_dir) if os.path.isdir(os.path.join(ndk_dir, d))]
                    if versions:
                        latest = sorted(versions, reverse=True)[0]
                        possible_paths.append(os.path.join(ndk_dir, latest))
            
            # Check Program Files
            program_files = os.environ.get('ProgramFiles', '')
            if program_files:
                android_dir = os.path.join(program_files, 'Android')
                if os.path.exists(android_dir):
                    for subdir in os.listdir(android_dir):
                        if 'ndk' in subdir.lower():
                            possible_paths.append(os.path.join(android_dir, subdir))
        
        else:  # macOS and Linux
            home = Path.home()
            # Check Android Studio default location
            sdk_path = home / 'Android' / 'Sdk'
            if sdk_path.exists():
                ndk_dir = sdk_path / 'ndk'
                if ndk_dir.exists():
                    versions = [d for d in os.listdir(ndk_dir) if os.path.isdir(os.path.join(ndk_dir, d))]
                    if versions:
                        latest = sorted(versions, reverse=True)[0]
                        possible_paths.append(str(ndk_dir / latest))
            
            # Check common installation locations
            common_paths = [
                home / 'Library' / 'Android' / 'sdk' / 'ndk',
                home / 'Android' / 'ndk',
                home / 'android-ndk-*',
                Path('/opt/android-ndk'),
                Path('/usr/local/lib/android/ndk')
            ]
            
            for path_pattern in common_paths:
                if '*' in str(path_pattern):
                    import glob
                    matches = glob.glob(str(path_pattern))
                    possible_paths.extend(matches)
                elif path_pattern.exists():
                    possible_paths.append(str(path_pattern))
        
        # Check environment variables
        env_ndk = os.environ.get('ANDROID_NDK_HOME')
        if env_ndk and os.path.exists(env_ndk):
            possible_paths.append(env_ndk)
            
        env_ndk_root = os.environ.get('ANDROID_NDK_ROOT')
        if env_ndk_root and os.path.exists(env_ndk_root):
            possible_paths.append(env_ndk_root)
        
        env_home = os.environ.get('ANDROID_HOME')
        if env_home:
            ndk_dir = os.path.join(env_home, 'ndk')
            if os.path.exists(ndk_dir):
                versions = [d for d in os.listdir(ndk_dir) if os.path.isdir(os.path.join(ndk_dir, d))]
                if versions:
                    latest = sorted(versions, reverse=True)[0]
                    possible_paths.append(os.path.join(ndk_dir, latest))
        
        # Remove duplicates and validate paths
        possible_paths = list(set(possible_paths))
        for path in possible_paths:
            if self.validate_ndk_path(path):
                self.ndk_path.set(path)
                self.log(f"Auto-detected NDK: {path}")
                return
        
        self.log("Could not auto-detect NDK. Please set manually or download.")
    
    def validate_ndk_path(self, path=None):
        if path is None:
            path = self.ndk_path.get()
            
        if not path:
            return False
            
        objcopy_path = self.get_objcopy_path(path)
        return os.path.exists(objcopy_path)
    
    def get_objcopy_path(self, ndk_path=None):
        if ndk_path is None:
            ndk_path = self.ndk_path.get()
        
        if not ndk_path:
            return ""
            
        # Determine platform-specific path components
        if os.name == 'nt':
            platform_dir = "windows-x86_64"
            exe_ext = ".exe"
        elif sys.platform == "darwin":
            platform_dir = "darwin-x86_64"
            exe_ext = ""
        else:
            platform_dir = "linux-x86_64"
            exe_ext = ""
        
        # Try llvm-objcopy first (newer NDK versions)
        objcopy_path = os.path.join(ndk_path, "toolchains", "llvm", "prebuilt", platform_dir, "bin", f"llvm-objcopy{exe_ext}")
        
        # If not found, try the old objcopy (older NDK versions)
        if not os.path.exists(objcopy_path):
            objcopy_path = os.path.join(ndk_path, "toolchains", "aarch64-linux-android-4.9", "prebuilt", platform_dir, "bin", f"aarch64-linux-android-objcopy{exe_ext}")
        
        return objcopy_path
    
    def browse_ndk(self):
        path = filedialog.askdirectory(title="Select NDK Directory")
        if path and self.validate_ndk_path(path):
            self.ndk_path.set(path)
        elif path:
            messagebox.showerror("Error", "Invalid NDK directory. llvm-objcopy not found.")
    
    def browse_source(self):
        path = filedialog.askdirectory(title="Select Source Directory")
        if path:
            self.source_dir.set(path)
    
    def browse_target(self):
        path = filedialog.askdirectory(title="Select Target Directory")
        if path:
            self.target_dir.set(path)
    
    def open_source(self):
        path = self.source_dir.get()
        if path and os.path.exists(path):
            try:
                if os.name == 'nt':
                    os.startfile(path)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', path])
                else:
                    subprocess.Popen(['xdg-open', path])
            except Exception as e:
                self.log(f"Error opening directory: {e}")
    
    def download_ndk(self):
        webbrowser.open("https://developer.android.com/ndk/downloads")
        self.log("Please download NDK and select the directory manually.")
    
    def start_alignment(self):
        if not self.ndk_path.get() or not self.validate_ndk_path():
            messagebox.showerror("Error", "Invalid NDK path")
            return
        
        if not self.source_dir.get() or not os.path.exists(self.source_dir.get()):
            messagebox.showerror("Error", "Invalid source directory")
            return
        
        if not self.target_dir.get():
            script_dir = os.path.dirname(os.path.abspath(__file__))
            default_target = os.path.join(script_dir, "Output")
            self.target_dir.set(default_target)
        
        # Create target directory if it doesn't exist
        if not os.path.exists(self.target_dir.get()):
            os.makedirs(self.target_dir.get())
        
        thread = threading.Thread(target=self.run_alignment)
        thread.daemon = True
        thread.start()
    
    def run_alignment(self):
        self.progress['value'] = 0
        self.progress_label['text'] = "0%"
        self.log("Starting alignment process...")
        
        try:
            source_dir = self.source_dir.get()
            target_dir = self.target_dir.get()
            objcopy = self.get_objcopy_path()
            
            if not os.path.exists(objcopy):
                self.log(f"Error: objcopy not found at {objcopy}")
                return
            
            so_patterns = ["*.so", "*.so.*"]
            so_files = []
            
            for pattern in so_patterns:
                for path in Path(source_dir).rglob(pattern):
                    if path.is_file():
                        so_files.append(path)
            
            so_files = list(set(so_files))
            
            if not so_files:
                self.log("No .so files found in source directory")
                return
            
            self.log(f"Found {len(so_files)} .so files")
            
            # Calculate total work
            selected_abis = [abi for abi, selected in self.selected_abis.items() if selected.get()]
            total_files = len(so_files) * len(selected_abis)
            processed_files = 0
            
            for abi in selected_abis:
                elf_format = self.abi_formats[abi]
                out_dir = os.path.join(target_dir, abi)
                
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                
                self.log(f"Processing ABI: {abi} (Format: {elf_format})")
                
                for so_file in so_files:
                    lib_name = os.path.basename(so_file)
                    src_file = str(so_file)
                    dst_file = os.path.join(out_dir, lib_name)
                    
                    self.log(f"  -> Aligning: {lib_name}")
                    
                    try:
                        tmp_bin = dst_file + ".bin"
                        
                        # First command: convert to binary with padding
                        cmd1 = [objcopy, "--output-target=binary", "--pad-to=16384", src_file, tmp_bin]
                        result1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=30)
                        
                        if result1.returncode != 0:
                            self.log(f"Error in first objcopy step for {lib_name}: {result1.stderr}")
                            continue
                        
                        # Second command: convert back to ELF format
                        cmd2 = [objcopy, "--input-target=binary", "--output-target=" + elf_format, tmp_bin, dst_file]
                        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
                        
                        if result2.returncode != 0:
                            self.log(f"Error in second objcopy step for {lib_name}: {result2.stderr}")
                        
                        # Clean up temporary file
                        if os.path.exists(tmp_bin):
                            os.remove(tmp_bin)
                        
                    except subprocess.TimeoutExpired:
                        self.log(f"Timeout processing {lib_name}")
                    except subprocess.CalledProcessError as e:
                        self.log(f"Error processing {lib_name}: {e.stderr if e.stderr else str(e)}")
                    except Exception as e:
                        self.log(f"Error processing {lib_name}: {str(e)}")
                    
                    # Update progress
                    processed_files += 1
                    if total_files > 0:
                        progress_percent = int((processed_files / total_files) * 100)
                        self.progress['value'] = progress_percent
                        self.progress_label['text'] = f"{progress_percent}%"
                        self.root.update_idletasks()
            
            self.log("✅ All libraries have been processed!")
            
            # Open output folder when done
            try:
                target_path = self.target_dir.get()
                if os.name == 'nt':
                    os.startfile(target_path)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', target_path])
                else:
                    subprocess.Popen(['xdg-open', target_path])
            except Exception as e:
                self.log(f"Note: Could not open output directory: {e}")
            
        except Exception as e:
            self.log(f"Error during alignment: {str(e)}")
        finally:
            self.progress['value'] = 100
            self.progress_label['text'] = "100%"
    
    def log(self, message):
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.delete(1.0, END)

def main():
    root = Tk()
    app = NDKAlignmentTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()